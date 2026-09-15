# Q4 projection maths

This note documents the simple linear projection used by the Lexeme Dashboard. It is kept outside the site so it is available as a reference without becoming part of the dashboard UI.

## What is being projected?

The dashboard uses the available **July to September 2026 overall edit counts** to estimate October to December 2026.

Current data:

| x | Month | y = overall edits |
|---:|---|---:|
| 0 | July 2026 | 144,843 |
| 1 | August 2026 | 312,613 |
| 2 | September 2026 | 176,408 |

The projection is deliberately simple. It is an indicator, not a promise or a statistically strong forecast.

## Linear regression

The fitted line has the form:

`ŷ = a + bx`

where:

- `ŷ` is the projected number of edits
- `x` is the month index
- `a` is the intercept
- `b` is the slope, or estimated change in edits per month

### 1. Calculate the slope

The least-squares slope is:

`b = Σ((xᵢ - x̄)(yᵢ - ȳ)) / Σ((xᵢ - x̄)²)`

For the three current points:

- `x̄ = (0 + 1 + 2) / 3 = 1`
- `ȳ = (144,843 + 312,613 + 176,408) / 3 = 211,288`

This gives:

`b = 15,782.5`

So the fitted trend is increasing by about **15,783 edits per month**.

### 2. Calculate the intercept

The intercept is:

`a = ȳ - bx̄`

Therefore:

`a = 211,288 - (15,782.5 × 1) = 195,505.5`

### 3. The resulting formula

The current projection line is:

`ŷ = 195,505.5 + 15,782.5x`

The `x` value continues from the same month index used for the July to September data:

- July = `0`
- August = `1`
- September = `2`
- October = `3`
- November = `4`
- December = `5`

### 4. Project Q4

**October**

`195,505.5 + (15,782.5 × 3) = 242,853`

**November**

`195,505.5 + (15,782.5 × 4) = 258,636`

**December**

`195,505.5 + (15,782.5 × 5) = 274,418`

The projected Q4 average is therefore approximately:

`(242,853 + 258,636 + 274,418) / 3 = 258,636`

## Why use this approach?

It gives a transparent baseline for answering: **"If the recent July to September trend continued roughly linearly, where would Q4 land?"**

It is intentionally not more complicated than that. There are only three observations, and the monthly values are quite volatile, so this should not be interpreted as a reliable forecast of actual future edits.

## How the site implements it

The dashboard's `buildProjection()` function:

1. Takes the available overall edit counts from July through December 2026.
2. Keeps the numeric July to September observations that are actually available.
3. Requires at least two observations before calculating a trend.
4. Calculates the least-squares slope and intercept.
5. Calculates future months through December 2026.
6. Rounds projected edit counts to whole numbers.
7. Prevents a negative projection by applying a minimum of zero.

The projection is only displayed when the **Show Q4 projection** toggle is enabled.
