# Lesson 36 — Practice: Hotel Booking System

> **Format:** problem statement. Time-box: 30 minutes.
> Read the prompt, draw the schema, then read the
> solution in [`code/solutions.py`](../code/solutions.py).

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

Design a data warehouse for a **hotel booking
system** (think Booking.com or a hotel chain's
internal system). The hotel has rooms, guests make
reservations, check in, stay, and check out. The
hotel wants to report on:

1. **Occupancy rate** — % of rooms occupied, by
   night, by room type.
2. **Revenue** — room revenue, F&B revenue, total
   revenue per available room (RevPAR).
3. **Booking lead time** — how far in advance do
   guests book? Average, by channel.
4. **Cancellation rate** — what % of bookings are
   cancelled, by lead time, by channel.
5. **Guest segmentation** — loyalty tier, repeat
   guest rate, segment by booking behavior.

The OLTP source tracks: hotels (id, name, city,
country, star_rating), rooms (room_id, hotel_id,
room_type, max_occupancy, base_price), guests
(guest_id, name, email, loyalty_tier, signup_date),
reservations (reservation_id, guest_id, hotel_id,
room_id, check_in_date, check_out_date, booking_date,
channel, status), and payments (payment_id,
reservation_id, amount, type, status).

---

## What to produce

1. **Discovery questions** — at least five.
2. **Requirements doc** — consumers, use cases,
   sources, and key facts.
3. **Star schema** — fact tables, dimensions, grain.
4. **SCD choices** — for each dim.
5. **Three SQL queries** — occupancy rate, RevPAR,
   cancellation rate.
6. **Tradeoffs** — at least two.

---

## Hints

- A reservation has a clear lifecycle: booked →
  checked in → checked out (or cancelled). The
  accumulating-snapshot fact fits this *perfectly*
  — the grain is "one row per reservation" and the
  milestones are book / check-in / check-out.
- Room inventory is a periodic-snapshot fact —
  one row per (room, night) with `occupied_flag`
  and `rate`.
- Revenue can be a *measure* on the reservation
  fact (sum of room rate × nights + F&B), or a
  separate fact joined to the reservation.
- Cancellation has its own analysis: by lead time,
  by channel, by guest segment.
- Loyalty tier is SCD 2 — a guest who upgrades
  from "silver" to "gold" mid-year should
  attribute Q1 stays to silver and Q3 stays to
  gold.

---

## Sample discovery questions

1. Is "reservation" a future-dated booking, the
   actual stay, or both? (Both — but the grain
   matters.)
2. Can a single reservation have multiple rooms?
   (Yes for group bookings.)
3. Is the cancellation rate "of all bookings" or
   "of bookings that should have happened" (i.e.,
   exclude no-shows)?
4. What is a "channel"? Direct, OTA (Expedia),
   GDS (Amadeus), wholesale?
5. Are rates dynamic (yield management) or fixed
   per room type?
6. Is there a separate "no-show" event, or is it
   a status on the reservation?
7. Are F&B and other ancillary revenues on the
   reservation or a separate fact?
8. Is loyalty tier SCD 2 (do we want to attribute
   Q1 stays to Q1 tier)?
9. What's the SLA for the warehouse? Hotel
   revenue reports are often end-of-day.
10. Are multi-night stays broken out per night
    (for occupancy) or treated as one row (for
    revenue)?

---

## Sample star schema

```
fact_reservations (accumulating snapshot)
   grain: one row per reservation
   measures: num_nights, num_rooms, total_room_revenue,
             total_fb_revenue, cancellation_lead_days
   milestones: book_date_key, check_in_date_key,
               check_out_date_key, cancel_date_key
   dimensions:
     dim_guest     (SCD 2; name, loyalty_tier, country, signup_date)
     dim_hotel     (SCD 1; name, city, country, star_rating)
     dim_room_type (SCD 1; type, max_occupancy, base_price)
     dim_channel   (SCD 1; channel, channel_category)
     dim_date      (conformed; role-played)

fact_room_nights (periodic snapshot)
   grain: one row per (room, night)
   measures: occupied_flag, rate_charged, was_cancelled
   dimensions:
     dim_hotel, dim_room, dim_date, dim_channel
```

`fact_reservations` is the central fact. `fact_room_nights`
is the daily-grain fact that supports the occupancy
report and is built by exploding reservations across
their date range.

---

## Sample SQL queries

**Occupancy rate by hotel and month:**

```sql
SELECT h.hotel_name, d.month,
       100.0 * SUM(r.occupied_flag) / COUNT(*) AS occupancy_pct
FROM fact_room_nights r
JOIN dim_hotel h ON r.hotel_key = h.hotel_key
JOIN dim_date  d ON r.date_key = d.date_key
WHERE d.year = 2024
GROUP BY h.hotel_name, d.month;
```

**RevPAR (Revenue per Available Room):**

```sql
SELECT h.hotel_name, d.month,
       SUM(r.rate_charged) / COUNT(*) AS revpar
FROM fact_room_nights r
JOIN dim_hotel h ON r.hotel_key = h.hotel_key
JOIN dim_date  d ON r.date_key = d.date_key
WHERE d.year = 2024
GROUP BY h.hotel_name, d.month;
```

(`COUNT(*)` is total available room-nights; `SUM(rate_charged)`
is total room revenue. RevPAR is the ratio.)

**Cancellation rate by channel:**

```sql
SELECT c.channel_name,
       100.0 * SUM(CASE WHEN r.status = 'cancelled' THEN 1 ELSE 0 END)
            / COUNT(*) AS cancel_pct
FROM fact_reservations r
JOIN dim_channel c ON r.channel_key = c.channel_key
WHERE r.book_date_key BETWEEN 20240101 AND 20241231
GROUP BY c.channel_name;
```

---

## Tradeoffs to call out

1. **Accumulating snapshot vs transactional for
   reservations.** I picked accumulating because
   the reservation has a clear lifecycle and the
   milestones (book, check-in, check-out) are
   queryable as separate date keys.
2. **Periodic snapshot for room nights vs derived
   from reservations.** I picked snapshot because
   it answers the "occupancy on a given night"
   question without a complex query, and it lets
   you compare to actual rooms (including
   out-of-order rooms, which a reservation
   derivation wouldn't capture).
3. **SCD 2 on guest.** Required for historical
   attribution of stays to loyalty tier.
4. **Channel as a separate dim vs a flag.** Channel
   has attributes (category, commission_pct) so a
   dim is appropriate. If channel were just
   "direct" vs "OTA," a flag would do.

---

## Try it

Set a 30-minute timer. Work the problem cold. Then
read [`code/solutions.py`](../code/solutions.py) and
[`tests/test_solutions.py`](../tests/test_solutions.py).

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
