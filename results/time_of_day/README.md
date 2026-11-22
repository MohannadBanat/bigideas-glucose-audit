# Time-of-day and meal-alignment gate check: results

Run on 22 Nov 2026 with `code/check_time_of_day.py` (seed 20261122) and
`code/plot_time_of_day.py`, using BIG IDEAs **v1.1.3**: `Demographics.csv` and
the `Food_Log_*` and `Dexcom_*` files for all 16 participants. They were
downloaded from physionet.org, and all 33 files match `SHA256SUMS.txt`.

This check fitted no model and touched no Empatica E4 data. It did read CGM
glucose values, so these outputs must be listed under "already seen by the
authors" in the OSF registration.

## Verdicts

| Question | Verdict | Evidence |
|---|---|---|
| Is clock time preserved after date-shifting? | **Yes, for all 16 participants.** | 15 of 16 have a median first food entry between 05:00 and 11:00. Participant 010 is the exception at 04:45, but that participant logs the same breakfast (Frosted Flakes and milk) at 04:29–05:34 on six days, and the CGM confirms meals at those times (below). That is an early riser, not a shifted clock. The script's fixed 05–11 rule flags 010 as "CHECK MANUALLY", and this paragraph records the manual decision. |
| Do the food log and the CGM share one clock? | **14 of 16 yes; 015 and 016 no.** | `alignment_by_participant.csv`, `fig_lag_sweep_minutes.png`, `fig_lag_sweep_days.png` |
| Can the TIME control (E3) go ahead? | **GO.** | It needs only clock time on the CGM and E4 streams, and that is preserved. |
| Can MEAL features be used? | **For 14 participants. 015 and 016 need a registered rule.** | See below. |

## How alignment was tested

Entries logged within 30 min of each other were merged into one meal event,
and events with fewer than 10 g of carbohydrate were dropped. For each event
the **rise** is the largest glucose value in the 2 h after the logged time,
minus the mean of the 15 min before it. Four checks follow:

1. **Coverage.** At least 80% of meal events fall inside the CGM recording.
2. **Meal response.** The mean rise at logged meal times is larger than at
   random times in the same recording (2,000 permutations, p < 0.05).
3. **Day shift.** Moving every meal by whole days (−21 to +21) does not beat a
   shift of 0. Only shifts that keep at least half of the events are compared.
4. **Minute shift.** The best shift within ±12 h is no more than 60 min from 0.

The check was built so that it can fail. It did fail for 2 participants, and
for 3 others under an earlier rule (see "Change made after the first run").

## Results by participant

The aligned participants show a mean rise of 28.8–47.1 mg/dL at logged meals,
against 11.8–22.3 mg/dL at random times (permutation p ≤ 0.0045). The best
minute shift lies between −30 and +15 min, which fits the usual gap between
logging a meal and the glucose rise.

- **015, food log outside the CGM recording.** Food is logged from 5 to 13 July
  2020, but the CGM runs from 19 to 27 July 2020. No logged meal falls inside
  the recording. A whole-day shift of 12–18 days recovers enough events to
  compare, but the best of them gives a 15.6 mg/dL rise. That is no larger
  than random times in the other recordings, so the true offset cannot be
  recovered from the data. Version 1.1.3 was released to fix misaligned
  food-log dates, and this participant still looks misaligned.
- **016, no meal response at the logged times.** The rise at logged meals is
  19.6 mg/dL against 19.1 at random times (p = 0.45). The sweep peaks at a
  shift of **−3 h** (31.7 mg/dL). [Guessing] That pattern fits a food log
  recorded in a time zone 3 h ahead of the CGM (Eastern against Pacific). It
  was found by searching many shifts, so it is a hypothesis, not a correction.
  Do not apply it unless the dataset authors confirm it.

## Change made after the first run (disclosed)

On the first run the day-shift check picked the best of all shifts that kept
at least 5 events. Participants 004, 005 and 012 then "failed" at shifts of −6,
−7 and +5 days. Those shifts kept only 6–7 events, against 17–33 at shift 0,
and at every well-supported shift, shift 0 was clearly the largest
(`lag_sweep_days.csv`). The rule was changed to compare only shifts that keep
at least half the events, and the 3 participants then passed. The figure
still draws the excluded shifts faintly, so the reader can see them. The
change was made after the data had been seen, so the registration must report
it.

## Cohort description (resolves next_steps #4)

`Demographics.csv` lists **9 female and 7 male** participants, with HbA1c of
5.3–6.4%. Any description of the cohort as female-only is wrong. With 7
males, sex alone splits the cohort into two groups of 9 and 7. That is
relevant to the identity shortcut (E3, H3).

## Data quirks the preprocessing must handle

- `Food_Log_003.csv` has **no header row** and only 11 columns (no `time_end`,
  `dietary_fiber` or `total_fat`). The script maps the columns from their
  values. For example, 8 nuggets give 19 g of carbohydrate, which matches 3
  nuggets giving 7.2 g for participant 001.
- 4 food logs name the clock column `time_of_day` and 11 name it `time`. Use
  `time_begin` (a full datetime), which every file has.
- `Food_Log_012.csv` has one row whose time cannot be parsed. It is dropped.
- The Dexcom files begin with 12 metadata and alert rows. Keep rows with
  `Event Type == "EGV"` only.
- **The AWS S3 mirror has no v1.1.3** (its newest version is 1.1.2, checked
  22 Nov 2026). The old `download_data.sh` would have "succeeded" with an
  empty folder. It now downloads from physionet.org.

## What the registration needs to say (proposed wording)

> Meal-derived features (MEAL set; experiments E4 and FULL-B) are computed only
> for participants whose food log passed the alignment check in
> `results/time_of_day/` (14 of 16; 015 and 016 excluded). Experiments that do
> not use MEAL features include all 16 participants. As a sensitivity
> analysis, E4 is repeated on the 14 aligned participants for all feature
> sets, so that comparisons are made on the same people.

## Files

| File | Contents |
|---|---|
| `summary.txt` | Printed output of the check |
| `meal_hours_by_participant.csv` | Clock-hour plausibility from the food logs |
| `alignment_by_participant.csv` | Checks 1–4 and the verdict for each participant |
| `lag_sweep_minutes.csv`, `lag_sweep_days.csv` | Rise statistic against shift |
| `glucose_by_hour.csv` | Mean CGM glucose by clock hour |
| `fig_lag_sweep_minutes.png`, `fig_lag_sweep_days.png` | Figures (one panel per participant) |
