# Product metrics

## Active user
Definition: a user is **active** on a given day if they trigger at least one
qualifying product event in that day, in the reporting timezone. Qualifying
events are: `course_viewed`, `lesson_completed`, `product_published`,
`checkout_completed`. A login on its own does not make a user active.

Monthly active users (MAU) counts distinct users active on at least one day in
the calendar month. MAU is not the sum of daily actives.

## Churn
Definition: a monthly subscription is **churned** in the month its paid access
ends and is not renewed within a 7-day grace period. Downgrades are not churn;
they are recorded as contraction.

Annual subscriptions are counted as churned in the month the term ends, not in
the month the cancellation was requested.

## Activation
A new account is **activated** when it publishes its first digital product.
Activation rate is measured over a 28-day window from signup.
