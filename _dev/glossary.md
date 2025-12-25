# Glossary of Terms

A comprehensive reference for technical terms, mathematical notation, and key concepts used throughout the Oracle framework.

---

## A

**Active Inference**  
A framework where organisms act to confirm their predictions, not just passively observe. Combines perception and action under a unified prediction principle.

**Adversarial Example**  
An input specifically crafted to fool a predictive system, often by adding imperceptible perturbations.

**Argmax (Argument of the Maximum)**  
The input value that produces the maximum output of a function. Formally: $\arg\max_x f(x)$ returns the $x$ that maximizes $f(x)$.

**Alpha**  
In finance: excess return beyond what would be expected given risk. In statistics: significance level for hypothesis testing (typically 0.05).

**AUC-ROC (Area Under Receiver Operating Characteristic Curve)**  
A metric measuring classification performance across all threshold settings. Perfect classifier: AUC = 1.0, random: AUC = 0.5.

---

## B

**Backtest**  
Simulating a trading strategy on historical data to evaluate performance before real deployment.

**Bayes Error Rate**  
The minimum possible error rate for a classification problem, arising from irreducible uncertainty in the data distribution.

**Bayes Optimal**  
A decision rule that minimizes expected loss given true probability distributions. The argmax with perfect scoring is Bayes optimal.

**Bias-Variance Tradeoff**  
Simple models have high bias (underfitting), complex models have high variance (overfitting). Optimal model balances both.

**Bootstrap**  
A statistical resampling technique: repeatedly sample with replacement from data to estimate distributions and confidence intervals.

---

## C

**Candidate Space ($\mathcal{C}$)**  
The set of all possible predictions or outputs the system can choose from (e.g., {up, down, flat}, all possible next words).

**CAPM (Capital Asset Pricing Model)**  
A model relating expected return of an asset to its systematic risk (beta) relative to the market.

**Calibration**  
How well predicted probabilities match observed frequencies. A calibrated model: if it predicts 70% probability, outcome occurs ~70% of the time.

**CVaR (Conditional Value at Risk)**  
Expected loss given that loss exceeds VaR threshold. Also called Expected Shortfall. More conservative than VaR.

**Context ($c$)**  
All available information used to make a prediction (e.g., recent prices, indicators, news, time of day).

---

## D

**Drawdown**  
Peak-to-trough decline in portfolio value. Maximum Drawdown (MDD) is the largest such decline over a period.

**Drift (Concept Drift)**  
Changes in the underlying data distribution over time, causing trained models to become less accurate.

---

## E

**Efficient Market Hypothesis (EMH)**  
Theory that asset prices reflect all available information, making consistent outperformance impossible.

**Empirical Risk Minimization (ERM)**  
Learning approach that chooses the model minimizing error on training data.

**Ensemble**  
Combining multiple models to reduce variance and improve robustness (e.g., random forests, boosting).

**Entropy**  
Measure of uncertainty or randomness in a distribution: $H(X) = -\sum_x P(x) \log P(x)$. Higher entropy = more unpredictable.

**Expected Value**  
Average outcome weighted by probabilities: $\mathbb{E}[X] = \sum_x P(x) \cdot x$

---

## F

**False Discovery Rate (FDR)**  
Expected proportion of false positives among rejected hypotheses. Used to correct for multiple testing.

**Feature Engineering**  
Creating informative input variables from raw data (e.g., computing RSI from prices).

**Free Energy Principle**  
Biological systems minimize surprise (free energy) by updating beliefs and taking actions to confirm predictions.

**F1-Score**  
Harmonic mean of precision and recall: $F1 = 2 \cdot \frac{PR}{P+R}$. Balances false positives and false negatives.

---

## G

**Generalization**  
A model's ability to perform well on new, unseen data (not just training data).

**Gödel's Incompleteness Theorems**  
Formal systems cannot prove all truths within themselves, and cannot prove their own consistency. Limits logical prediction.

**Gradient Descent**  
Optimization algorithm that iteratively adjusts parameters in the direction that reduces loss.

---

## H

**Halting Problem**  
Fundamental result: no algorithm can determine whether arbitrary programs will halt or run forever. Limits computability of predictions.

**Hyperparameter**  
Configuration setting for a learning algorithm (e.g., learning rate, number of layers) not learned from data.

---

## I

**Information Ratio**  
Ratio of active return to tracking error. Measures risk-adjusted performance relative to a benchmark.

**In-Sample**  
Data used to train a model. Performance on in-sample data is optimistically biased.

**Irreducible Uncertainty**  
Randomness that cannot be eliminated even with perfect information (e.g., quantum mechanics, truly random processes).

---

## K

**Kelly Criterion**  
Optimal bet sizing formula: $f^* = \frac{p(b+1)-1}{b}$ for discrete bets, $f^* = \frac{\mu}{\sigma^2}$ for continuous returns.

**Kolmogorov Complexity**  
Length of the shortest program that produces a given string. Random strings are incompressible.

---

## L

**Latency**  
Time delay between data arrival and action execution. Critical in high-frequency trading.

**Leverage**  
Using borrowed capital to amplify returns (and risks). Leverage of 2× means $1 borrowed for every $1 of equity.

**Log-Loss (Cross-Entropy Loss)**  
$-\sum_i \log P(\text{true class}_i)$. Penalizes confident wrong predictions heavily.

**Look-Ahead Bias**  
Using future information not available at prediction time, artificially inflating backtested performance.

---

## M

**Market Impact**  
Price movement caused by a large trade. Larger trades have higher slippage.

**Markowitz Portfolio**  
Mean-variance optimal portfolio balancing expected return and risk.

**Mutual Information**  
$I(X;Y) = H(X) - H(X \mid Y)$. Measures how much knowing $Y$ reduces uncertainty about $X$.

---

## N

**No-Free-Lunch Theorem**  
Averaged over all possible problems, all optimization algorithms perform equally. Specialization is necessary.

**Normalization**  
Scaling data to a standard range (e.g., mean=0, std=1) to improve training stability.

---

## O

**Overfitting**  
When a model learns training data too well, including noise, harming generalization to new data.

**Out-of-Sample**  
Data not used in training, providing unbiased performance estimates.

---

## P

**PAC Learning (Probably Approximately Correct)**  
Framework guaranteeing that with sufficient data, learned model will be close to optimal with high probability.

**Precision**  
$\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$. Among predicted positives, how many are correct?

**Predictive Coding**  
Neural theory: brain generates predictions and updates them based on prediction errors.

**P vs NP**  
Unsolved: Can every problem whose solution is quickly verifiable also be quickly solved? Impacts optimal learning complexity.

---

## Q

**Qualia**  
Subjective, conscious experiences (e.g., the "redness" of red, the feeling of pain). The "hard problem" of consciousness.

---

## R

**Rademacher Complexity**  
Measure of a function class's ability to fit random noise. Higher complexity → more overfitting risk.

**Recall (Sensitivity)**  
$\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$. Among actual positives, how many were detected?

**Regime**  
Distinct market condition (e.g., bull/bear, high/low volatility) requiring different strategies.

**Regularization**  
Adding penalty to complex models ($\lambda \Omega(w)$) to prevent overfitting.

**Risk Parity**  
Portfolio allocation where each asset contributes equally to total risk.

---

## S

**Sample Complexity**  
Number of training examples needed to learn a model to a given accuracy level.

**Scoring Function ($S(x \mid c)$)**  
Function assigning a value/probability to each candidate given context. Core of the argmax equation.

**Sharpe Ratio**  
$\frac{\mu - r_f}{\sigma}$. Risk-adjusted return metric. Higher is better. >1 is good, >2 is excellent.

**Slippage**  
Difference between expected and actual execution price due to market impact and timing.

**Sortino Ratio**  
Like Sharpe, but only penalizes downside volatility (ignores upside).

**Stochastic**  
Random, probabilistic. Opposite of deterministic.

---

## T

**Transaction Costs**  
Fees, spreads, and market impact paid when trading. Can erode strategy profitability.

**Turing Machine**  
Abstract computational model. Turing-complete systems can compute anything computable, but face Halting Problem limits.

---

## U

**Underfitting**  
Model is too simple to capture patterns in data, resulting in high error on both training and test sets.

**Utility Function**  
Function mapping outcomes to values/preferences. Rational agents maximize expected utility.

---

## V

**VaR (Value at Risk)**  
Maximum expected loss at a confidence level. 95% VaR of $100k means 5% chance of losing more than $100k.

**VC Dimension (Vapnik-Chervonenkis Dimension)**  
Measure of model complexity. Higher VC dimension requires more training data.

**Volatility**  
Standard deviation of returns. Higher volatility = higher risk.

---

## W

**Walk-Forward Testing**  
Backtesting with sequential train-test splits, mimicking real-world deployment without look-ahead bias.

**Win Rate**  
Percentage of trades that are profitable. High win rate doesn't guarantee profitability (depends on win/loss magnitudes).

---

## Notation Guide

### Greek Letters
- $\alpha$ - Significance level, learning rate, or alpha (excess return)
- $\beta$ - Systematic risk measure (CAPM)
- $\gamma$ - Discount factor, risk aversion parameter
- $\delta$ - Confidence parameter, small perturbation
- $\epsilon$ - Error tolerance, approximation error
- $\lambda$ - Regularization parameter, Lyapunov exponent
- $\mu$ - Mean, expected return
- $\sigma$ - Standard deviation, volatility
- $\Sigma$ - Covariance matrix
- $\pi$ - Policy function
- $\theta$ - Parameter vector
- $\Omega$ - Regularization term

### Symbols
- $\hat{x}$ - Predicted/estimated value (hat denotes estimate)
- $x^*$ - Optimal value (star denotes optimality)
- $\mathbb{E}[\cdot]$ - Expected value
- $\mathbb{P}(\cdot)$ - Probability
- $\arg\max$ - Argument that maximizes
- $\arg\min$ - Argument that minimizes
- $\sim$ - Distributed as (e.g., $X \sim N(0,1)$)
- $\propto$ - Proportional to
- $\approx$ - Approximately equal
- $\equiv$ - Defined as, equivalent to
- $\in$ - Element of (membership)
- $\subset$ - Subset of
- $\mathcal{C}$ - Candidate space
- $\mathcal{X}$ - Context space
- $\mathcal{S}$ - Scoring function class

### Operators
- $\log$ - Natural logarithm (ln)
- $\sum$ - Summation
- $\prod$ - Product
- $\max$ - Maximum value
- $\min$ - Minimum value
- $\nabla$ - Gradient
- $\partial$ - Partial derivative
- $\int$ - Integral

---

## Acronyms

**AI** - Artificial Intelligence  
**AGI** - Artificial General Intelligence  
**AST** - Abstract Syntax Tree  
**ATR** - Average True Range  
**CAPM** - Capital Asset Pricing Model  
**CV** - Cross-Validation  
**CVaR** - Conditional Value at Risk  
**EMA** - Exponential Moving Average  
**EMH** - Efficient Market Hypothesis  
**ERM** - Empirical Risk Minimization  
**FDR** - False Discovery Rate  
**HFT** - High-Frequency Trading  
**IDE** - Integrated Development Environment  
**LSTM** - Long Short-Term Memory (neural network)  
**MACD** - Moving Average Convergence Divergence  
**MDD** - Maximum Drawdown  
**MDL** - Minimum Description Length  
**ML** - Machine Learning  
**NLP** - Natural Language Processing  
**OHLC** - Open, High, Low, Close (price data)  
**PAC** - Probably Approximately Correct  
**PCA** - Principal Component Analysis  
**RSI** - Relative Strength Index  
**SMA** - Simple Moving Average  
**SNR** - Signal-to-Noise Ratio  
**TWAP** - Time-Weighted Average Price  
**VaR** - Value at Risk  
**VC** - Vapnik-Chervonenkis  
**VWAP** - Volume-Weighted Average Price  

---

## Key Concepts Summary

**The Argmax Equation:**
$$\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$$
Choose the candidate with the highest score given context.

**Bayes Optimal Scoring:**
$$S^*(x \mid c) = P(x \mid c)$$
Perfect scoring function is the true conditional probability.

**Fundamental Tradeoff:**
- More data → better generalization (to a point)
- More features → better expressiveness but higher sample complexity
- More complexity → better fit but higher overfitting risk

**Core Principle:**
> Prediction systems work because real problems have structure.  
> They fail because the world is not fully observable and constantly changing.

---

This glossary is a living document. Terms will be added as the framework evolves.
