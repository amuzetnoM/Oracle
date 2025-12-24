# Risk Management and Portfolio Theory

This document establishes the formal mathematical framework for translating predictions into risk-adjusted trading decisions, bridging the argmax equation to real-world portfolio management.

---

## 1. From Prediction to Action: The Decision Problem

### 1.1 The Translation Challenge

The argmax equation gives us a prediction:

$$\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$$

But trading requires decisions:
- **How much** to allocate?
- **When** to enter/exit?
- **What** risk to accept?

This requires a **utility function** that maps predictions to actions while managing risk.

---

## 2. Portfolio Theory Foundations

### 2.1 Markowitz Mean-Variance Framework

**Definition 2.1 (Portfolio Optimization)**  
Given $N$ assets with expected returns $\mu = [\mu_1, ..., \mu_N]$ and covariance matrix $\Sigma$, the optimal portfolio weights $w$ solve:

$$\max_w \; w^T \mu - \frac{\lambda}{2} w^T \Sigma w$$

subject to:
$$\sum_{i=1}^N w_i = 1, \quad w_i \geq 0$$

where $\lambda$ is the risk aversion parameter.

---

### 2.2 The Efficient Frontier

**Theorem 2.1 (Two-Fund Separation)**  
Every optimal portfolio is a linear combination of:
1. The **minimum variance portfolio**
2. The **tangency portfolio** (maximum Sharpe ratio)

**Sharpe Ratio:**
$$SR = \frac{\mu - r_f}{\sigma}$$

where $r_f$ is the risk-free rate.

---

### 2.3 Capital Asset Pricing Model (CAPM)

**Theorem 2.2 (CAPM)**  
The expected return of asset $i$ is:

$$\mathbb{E}[r_i] = r_f + \beta_i (\mathbb{E}[r_m] - r_f)$$

where:
- $\beta_i = \frac{\text{Cov}(r_i, r_m)}{\text{Var}(r_m)}$ measures systematic risk
- $r_m$ is the market return

**Implication:**  
Only systematic risk is rewarded; idiosyncratic risk can be diversified away.

---

## 3. Risk Measures and Constraints

### 3.1 Value at Risk (VaR)

**Definition 3.1 (VaR)**  
The Value at Risk at confidence level $\alpha$ is:

$$\text{VaR}_\alpha = \inf\{l : P(\text{Loss} \leq l) \geq \alpha\}$$

**Example:**  
95% VaR = $100,000 means there's a 5% chance of losing more than $100,000.

**Limitations:**
- Not coherent (fails subadditivity)
- Ignores tail behavior beyond threshold
- Can encourage risk concentration

---

### 3.2 Conditional Value at Risk (CVaR)

**Definition 3.2 (CVaR / Expected Shortfall)**  
The expected loss given that VaR is exceeded:

$$\text{CVaR}_\alpha = \mathbb{E}[\text{Loss} \mid \text{Loss} \geq \text{VaR}_\alpha]$$

**Properties:**
- ✅ Coherent risk measure (satisfies all axioms)
- ✅ Captures tail risk
- ✅ Convex optimization-friendly

**Theorem 3.1 (CVaR Optimization)**  
Minimizing CVaR can be formulated as a linear program:

$$\min_{w, \zeta} \left\{\zeta + \frac{1}{\alpha} \mathbb{E}[\max(L(w) - \zeta, 0)]\right\}$$

---

### 3.3 Maximum Drawdown

**Definition 3.3 (Maximum Drawdown)**  
The largest peak-to-trough decline:

$$\text{MDD} = \max_{t' \leq t} \left[\frac{\text{Peak}_{t'} - \text{Value}_t}{\text{Peak}_{t'}}\right]$$

**Practical Constraint:**  
Many institutional mandates limit maximum drawdown (e.g., "No more than 15% loss from peak").

---

### 3.4 Risk Parity

**Definition 3.4 (Risk Contribution)**  
The risk contribution of asset $i$ is:

$$RC_i = w_i \frac{\partial \sigma_p}{\partial w_i} = w_i \frac{(\Sigma w)_i}{\sigma_p}$$

**Risk Parity Principle:**  
Allocate such that all assets contribute equally to portfolio risk:

$$RC_1 = RC_2 = ... = RC_N$$

---

## 4. Integrating Predictions with Risk Management

### 4.1 Kelly Criterion

**Theorem 4.1 (Kelly Optimal Bet Size)**  
For a bet with probability $p$ of winning, odds $b:1$, the optimal fraction to wager is:

$$f^* = \frac{p(b+1) - 1}{b}$$

**Generalized Kelly (Continuous):**  
For normal returns with expected return $\mu$ and variance $\sigma^2$:

$$f^* = \frac{\mu}{\ \sigma^2}$$

**Practical Modification (Fractional Kelly):**  
Use $f = \frac{1}{2}f^*$ or $f = \frac{1}{4}f^*$ to reduce volatility and account for estimation error.

---

### 4.2 Prediction-Weighted Allocation

**Framework:**  
Given argmax prediction $\hat{x}$ with confidence $S(\hat{x} \mid c)$, define position size:

$$w = f(\text{confidence}) \cdot g(\text{expected return}) \cdot h(\text{risk})$$

**Example Formulation:**

$$w = \min\left\{\frac{S(\hat{x} \mid c) \cdot \mathbb{E}[R_{\hat{x}}]}{\sigma^2}, w_{\max}\right\}$$

where $w_{\max}$ is the maximum position limit.

---

### 4.3 Multi-Asset Integration

**Problem:**  
Given predictions for $N$ assets: $\{\hat{x}_1, ..., \hat{x}_N\}$ with confidences $\{S_1, ..., S_N\}$.

**Solution:**  
Optimize portfolio weights subject to risk constraints:

$$\max_w \sum_{i=1}^N w_i \mathbb{E}[R_i \mid \hat{x}_i] S_i$$

subject to:
$$w^T \Sigma w \leq \sigma_{\max}^2, \quad \sum w_i = 1, \quad |w_i| \leq w_{\max}$$

---

## 5. Transaction Costs and Market Impact

### 5.1 Transaction Cost Model

**Linear Cost:**
$$\text{Cost} = c \cdot |\Delta w|$$

where $\Delta w$ is the change in position and $c$ is the cost rate (bps).

**Quadratic Market Impact:**
$$\text{Cost} = c_1 |\Delta w| + c_2 (\Delta w)^2$$

Models permanent price impact for large trades.

---

### 5.2 Optimal Execution

**Almgren-Chriss Model:**  
Minimize the trade-off between market impact and timing risk:

$$\min_{\{x_t\}} \mathbb{E}[\text{Cost}] + \lambda \text{Var}[\text{Cost}]$$

where $\{x_t\}$ is the trade schedule.

**Result:**  
Trade schedule follows exponential decay or square root profile depending on market conditions.

---

### 5.3 Position Sizing with Friction

**Adjusted Position:**  
Only rebalance if expected profit exceeds transaction costs:

$$\text{Rebalance if:} \quad |\mathbb{E}[R \mid \hat{x}] \cdot S(\hat{x} \mid c)| \cdot |w_{\text{new}} - w_{\text{old}}| > c \cdot |w_{\text{new}} - w_{\text{old}}|$$

Equivalently:
$$|\mathbb{E}[R] \cdot S| > c$$

---

## 6. Dynamic Rebalancing and Adaptation

### 6.1 Time-Varying Predictions

**Problem:**  
Predictions $\hat{x}_t$ change over time as context $c_t$ evolves.

**Continuous Rebalancing:**

$$w_t = \arg\max_w \mathbb{E}[R_t \mid \hat{x}_t, c_t] - \frac{\lambda}{2} w^T \Sigma_t w - \text{TC}(w_t, w_{t-1})$$

---

### 6.2 Regime-Dependent Strategies

**Multi-Regime Model:**  
Define regimes $\mathcal{R} = \{\text{bull, bear, volatile, calm}\}$.

Predict regime:
$$\hat{r}_t = \arg\max_{r \in \mathcal{R}} S(r \mid c_t)$$

Use regime-specific strategies:
$$w_t = w^{(\hat{r}_t)}$$

---

### 6.3 Online Portfolio Selection

**Exponential Gradient Algorithm:**

$$w_{t+1} = w_t \cdot \exp(\eta \cdot r_t) / Z$$

where $Z$ is normalization and $\eta$ is learning rate.

**Guarantee:**  
Achieves regret bound $O(\sqrt{T})$ relative to best fixed strategy in hindsight.

---

## 7. Backtesting Framework

### 7.1 Walk-Forward Validation

**Procedure:**
1. Train scoring function on data $[t_0, t_1]$
2. Test on out-of-sample period $[t_1, t_2]$
3. Roll window forward: train on $[t_1, t_2]$, test on $[t_2, t_3]$
4. Aggregate performance across all test periods

**Critical:**  
Never use future information (no look-ahead bias).

---

### 7.2 Performance Metrics

**Sharpe Ratio:**
$$SR = \frac{\text{Mean Return}}{\text{Std Dev of Returns}} \cdot \sqrt{252}$$

(Annualized for daily returns)

**Sortino Ratio:**
$$\text{Sortino} = \frac{\text{Mean Return}}{\text{Downside Deviation}}$$

Only penalizes downside volatility.

**Calmar Ratio:**
$$\text{Calmar} = \frac{\text{Annual Return}}{\text{Maximum Drawdown}}$$

**Information Ratio:**
$$IR = \frac{\text{Active Return}}{\text{Tracking Error}}$$

---

### 7.3 Statistical Significance

**Hypothesis Test:**  
$H_0$: Strategy has zero alpha (no skill)

**T-Statistic:**
$$t = \frac{\bar{r}}{\hat{\sigma} / \sqrt{n}}$$

**Multiple Testing Correction:**  
Use Bonferroni or False Discovery Rate (FDR) correction when testing multiple strategies.

**Danger:**  
Overfitting from excessive backtesting ("p-hacking"). Require out-of-sample validation.

---

## 8. Market Microstructure Considerations

### 8.1 Bid-Ask Spread

**Effective Cost:**  
Buying at ask, selling at bid creates immediate loss:

$$\text{Spread Cost} = \frac{\text{Ask} - \text{Bid}}{\text{Mid}} \approx 2 \times \text{half-spread}$$

**Incorporation:**  
Adjust expected returns:

$$\mathbb{E}[R]_{\text{net}} = \mathbb{E}[R]_{\text{gross}} - \text{Spread Cost}$$

---

### 8.2 Liquidity Constraints

**Volume Limit:**  
Cannot trade more than $\alpha$ of daily volume without severe impact:

$$|w_{\text{new}} - w_{\text{old}}| \leq \alpha \cdot \text{ADV} \cdot \text{price}$$

where ADV = average daily volume.

---

### 8.3 Slippage Model

**Expected Slippage:**

$$\text{Slippage} = \gamma \cdot \left(\frac{|\Delta w|}{\text{ADV}}\right)^\beta$$

Typical values: $\beta \in [0.5, 1.5]$

---

## 9. Advanced: Optimal Stopping and Options

### 9.1 Entry/Exit Timing

**Optimal Stopping Problem:**  
Given prediction stream $\{\hat{x}_t\}_{t=1}^T$, when to trade?

**Threshold Policy:**  
Enter position if:

$$S(\hat{x}_t \mid c_t) \geq \theta_{\text{entry}}$$

Exit if:
$$S(\hat{x}_t \mid c_t) \leq \theta_{\text{exit}}$$

Optimize $(\theta_{\text{entry}}, \theta_{\text{exit}})$ to maximize risk-adjusted returns.

---

### 9.2 Options as Risk Management

**Put Options:**  
Buy puts to limit downside:

$$\text{Protected Payoff} = \max(V_T, K) - \text{Premium}$$

where $K$ is strike price.

**Cost-Benefit:**  
Premium paid vs. tail risk eliminated.

**Dynamic Hedging:**  
Delta-hedge to maintain market neutrality while extracting alpha from predictions.

---

## 10. Practical Implementation Checklist

### Pre-Trade:
- ✅ Validate prediction confidence exceeds threshold
- ✅ Check position sizing against risk limits
- ✅ Verify liquidity is sufficient
- ✅ Calculate transaction costs
- ✅ Ensure no regulatory violations

### During Trade:
- ✅ Use limit orders to control slippage
- ✅ Split large orders (TWAP/VWAP algorithms)
- ✅ Monitor for adverse price movements
- ✅ Update confidence in real-time

### Post-Trade:
- ✅ Record actual execution price and costs
- ✅ Update performance metrics
- ✅ Analyze prediction accuracy
- ✅ Feed results back to scoring function

---

## 11. Regulatory and Compliance

### 11.1 Risk Limits

**Regulatory Capital Requirements (Basel III):**
$$\text{Capital Requirement} = \max\{\text{VaR}_{99}, \text{Stressed VaR}_{99}\} \times 3$$

**Position Limits:**  
Many markets impose limits on contract holdings.

---

### 11.2 Market Manipulation

**Illegal Activities:**
- Spoofing (placing orders with intent to cancel)
- Layering (creating false depth)
- Pump and dump schemes

**Compliance:**  
Ensure trading algorithm does not inadvertently create manipulative patterns.

---

## 12. Summary: The Complete Pipeline

### Prediction → Decision Flow:

1. **Predict:** $\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$
2. **Estimate Return:** $\mathbb{E}[R \mid \hat{x}]$ and $\sigma$
3. **Compute Confidence:** $p = S(\hat{x} \mid c)$
4. **Calculate Position:**  
   $$w = \min\left\{\frac{p \cdot \mathbb{E}[R]}{\lambda \sigma^2}, w_{\max}\right\}$$
5. **Adjust for Costs:**  
   $$w_{\text{net}} = w \text{ if } |w \cdot \mathbb{E}[R]| > \text{TC}, \text{ else } 0$$
6. **Risk Check:**  
   Verify $\text{VaR}, \text{CVaR}, \text{MDD}$ constraints
7. **Execute:**  
   Optimal execution strategy
8. **Monitor & Update:**  
   Track performance, update scoring function

---

## Key Principles:

> **Never risk more than you can afford to lose**  
> **Size positions by confidence and risk, not by hunch**  
> **Transaction costs are real — account for them**  
> **Diversification is the only free lunch**  
> **What gets measured gets managed**

---

## References

1. Markowitz, H. (1952). *Portfolio Selection*
2. Sharpe, W. F. (1964). *Capital Asset Prices: A Theory of Market Equilibrium*
3. Kelly, J. L. (1956). *A New Interpretation of Information Rate*
4. Almgren, R., & Chriss, N. (2001). *Optimal Execution of Portfolio Transactions*
5. Rockafellar, R. T., & Uryasev, S. (2000). *Optimization of Conditional Value-at-Risk*
6. Thorp, E. O. (2006). *The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market*
7. Grinold, R. C., & Kahn, R. N. (1999). *Active Portfolio Management*
