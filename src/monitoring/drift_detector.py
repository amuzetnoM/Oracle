"""
Drift Detector

Detects distribution drift in data and predictions.
Helps identify when models need retraining.
"""

import numpy as np
from typing import Optional, Dict, List
from scipy import stats


class DriftDetector:
    """
    Detect distribution drift in data streams.
    
    Uses statistical tests to detect when data distribution changes.
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        warning_threshold: float = 0.05,
        drift_threshold: float = 0.01
    ):
        """
        Initialize drift detector.
        
        Args:
            window_size: Size of reference window
            warning_threshold: P-value threshold for warning
            drift_threshold: P-value threshold for drift detection
        """
        self.window_size = window_size
        self.warning_threshold = warning_threshold
        self.drift_threshold = drift_threshold
        
        self.reference_data: Optional[np.ndarray] = None
        self.drift_detected = False
        self.warning_detected = False
    
    def set_reference(self, data: np.ndarray):
        """
        Set reference distribution.
        
        Args:
            data: Reference data
        """
        self.reference_data = np.array(data[-self.window_size:])
        self.drift_detected = False
        self.warning_detected = False
    
    def detect_ks_test(
        self,
        new_data: np.ndarray
    ) -> Dict[str, any]:
        """
        Detect drift using Kolmogorov-Smirnov test.
        
        Args:
            new_data: New data to test
        
        Returns:
            Dictionary with test results
        """
        if self.reference_data is None:
            self.set_reference(new_data)
            return {
                'drift': False,
                'warning': False,
                'p_value': 1.0,
                'statistic': 0.0
            }
        
        # Perform KS test
        statistic, p_value = stats.ks_2samp(
            self.reference_data,
            new_data
        )
        
        drift = p_value < self.drift_threshold
        warning = p_value < self.warning_threshold and not drift
        
        self.drift_detected = drift
        self.warning_detected = warning
        
        return {
            'drift': drift,
            'warning': warning,
            'p_value': float(p_value),
            'statistic': float(statistic)
        }
    
    def detect_population_stability_index(
        self,
        new_data: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, any]:
        """
        Detect drift using Population Stability Index (PSI).
        
        PSI measures the shift in distribution between two samples.
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Small change
        PSI >= 0.2: Significant change
        
        Args:
            new_data: New data to test
            n_bins: Number of bins for discretization
        
        Returns:
            Dictionary with PSI results
        """
        if self.reference_data is None:
            self.set_reference(new_data)
            return {
                'drift': False,
                'warning': False,
                'psi': 0.0
            }
        
        # Create bins based on reference data
        _, bin_edges = np.histogram(self.reference_data, bins=n_bins)
        
        # Calculate distributions
        ref_counts, _ = np.histogram(self.reference_data, bins=bin_edges)
        new_counts, _ = np.histogram(new_data, bins=bin_edges)
        
        # Convert to percentages
        ref_pct = ref_counts / len(self.reference_data)
        new_pct = new_counts / len(new_data)
        
        # Avoid division by zero
        ref_pct = np.where(ref_pct == 0, 0.0001, ref_pct)
        new_pct = np.where(new_pct == 0, 0.0001, new_pct)
        
        # Calculate PSI
        psi = np.sum((new_pct - ref_pct) * np.log(new_pct / ref_pct))
        
        # Interpret PSI
        drift = psi >= 0.2
        warning = 0.1 <= psi < 0.2
        
        self.drift_detected = drift
        self.warning_detected = warning
        
        return {
            'drift': drift,
            'warning': warning,
            'psi': float(psi)
        }
    
    def detect_mean_shift(
        self,
        new_data: np.ndarray,
        threshold_std: float = 2.0
    ) -> Dict[str, any]:
        """
        Detect drift by checking mean shift.
        
        Args:
            new_data: New data to test
            threshold_std: Number of standard deviations for drift
        
        Returns:
            Dictionary with mean shift results
        """
        if self.reference_data is None:
            self.set_reference(new_data)
            return {
                'drift': False,
                'warning': False,
                'shift': 0.0
            }
        
        ref_mean = np.mean(self.reference_data)
        ref_std = np.std(self.reference_data, ddof=1)
        new_mean = np.mean(new_data)
        
        # Calculate shift in standard deviations
        shift = abs(new_mean - ref_mean) / ref_std if ref_std > 0 else 0
        
        drift = shift >= threshold_std
        warning = shift >= threshold_std * 0.75 and not drift
        
        self.drift_detected = drift
        self.warning_detected = warning
        
        return {
            'drift': drift,
            'warning': warning,
            'shift': float(shift),
            'ref_mean': float(ref_mean),
            'new_mean': float(new_mean)
        }
    
    def detect_variance_change(
        self,
        new_data: np.ndarray,
        threshold_ratio: float = 2.0
    ) -> Dict[str, any]:
        """
        Detect change in variance.
        
        Args:
            new_data: New data to test
            threshold_ratio: Variance ratio threshold for drift
        
        Returns:
            Dictionary with variance change results
        """
        if self.reference_data is None:
            self.set_reference(new_data)
            return {
                'drift': False,
                'warning': False,
                'ratio': 1.0
            }
        
        ref_var = np.var(self.reference_data, ddof=1)
        new_var = np.var(new_data, ddof=1)
        
        # Variance ratio
        ratio = max(new_var, ref_var) / max(min(new_var, ref_var), 1e-10)
        
        drift = ratio >= threshold_ratio
        warning = ratio >= threshold_ratio * 0.75 and not drift
        
        self.drift_detected = drift
        self.warning_detected = warning
        
        return {
            'drift': drift,
            'warning': warning,
            'ratio': float(ratio),
            'ref_variance': float(ref_var),
            'new_variance': float(new_var)
        }
    
    def detect_comprehensive(
        self,
        new_data: np.ndarray
    ) -> Dict[str, any]:
        """
        Run comprehensive drift detection with multiple tests.
        
        Args:
            new_data: New data to test
        
        Returns:
            Dictionary with all test results
        """
        ks_result = self.detect_ks_test(new_data)
        psi_result = self.detect_population_stability_index(new_data)
        mean_result = self.detect_mean_shift(new_data)
        var_result = self.detect_variance_change(new_data)
        
        # Overall drift if any test detects drift
        overall_drift = any([
            ks_result['drift'],
            psi_result['drift'],
            mean_result['drift'],
            var_result['drift']
        ])
        
        # Overall warning if any test warns
        overall_warning = any([
            ks_result['warning'],
            psi_result['warning'],
            mean_result['warning'],
            var_result['warning']
        ])
        
        return {
            'drift_detected': overall_drift,
            'warning_detected': overall_warning,
            'ks_test': ks_result,
            'psi_test': psi_result,
            'mean_shift': mean_result,
            'variance_change': var_result
        }
    
    def update_reference(self, new_data: np.ndarray):
        """
        Update reference data with new data.
        
        Use after confirming drift and retraining model.
        
        Args:
            new_data: New data to use as reference
        """
        self.set_reference(new_data)
