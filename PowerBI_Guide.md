# Sustainability Power BI preparation

Source: https://github.com/chinl00n/capstone/tree/main (retrieved 31 October 2026).
Historical coverage: 173 countries, 2000–2018, 3,287 country-year rows, 47 numeric indicators and two annual classifications.

## Start here
1. Extract this ZIP to a permanent folder.
2. In Power BI Desktop select Get data > Text/CSV and import Sustainability_Joined.csv for the easiest single-table report. Use UTF-8 and comma delimiter. Set Country Code, Country Name, Continent, World Regions and classifications to Text; Year to Whole number; indicators to Decimal number. Empty numeric cells must remain null, never zero.
3. For a flexible indicator dashboard instead import FactIndicators, DimCountry, DimYear and DimIndicator CSVs. Use the relationships below. Do not also load the joined table into this model, or connect both fact layouts together.
4. Use Power Query to assign Value as Decimal number, HasValue and Year as Whole number, and remaining fields as Text. Disable automatic summarization for keys and years. Hide technical keys from report users.

## Recommended relationships
All relationships are active, one-to-many, single direction from dimension to fact:

| One side | Many side |
|---|---|
| DimCountry[Country Code] | FactIndicators[Country Code] |
| DimYear[Year] | FactIndicators[Year] |
| DimIndicator[IndicatorKey] | FactIndicators[IndicatorKey] |

DimYear is a year selector, not a daily date table; do not mark it as a date table. IncomeClassification and RegimeType belong to the fact because they vary by year. The alternative FactCountryYear table has one country-year row, short indicator columns I01–I47, and the same country/year relationships. DimIndicator maps every short name to its full original indicator label.

## Cleaning decisions and checks
- No country-year records removed: 3,287 in and out; no duplicate country-year keys.
- Deduplicated Country lookup from 3,287 to 173 records. Collapsed Continent lookup to 173 records only after verifying non-null attributes agree within country.
- Two missing TLS geography records resolved using the same country's explicit non-null classifications elsewhere in the supplied reference file. No external geographic assumptions.
- Country joins are validated many-to-one and retain all original rows. No unmatched countries.
- Energy (two indicators) and Electricity (one indicator) match the main data exactly on country-year. No discrepancies and no measurement replacements required. They are integrated once, avoiding duplicate indicator columns.
- Trimmed headings and text; uppercased country codes; enforced integer years.
- 27,490 missing numeric observations retained as null. No interpolation, mean replacement, forward filling, or invented zeros.
- Zero range flags for the explicitly bounded percentage/index checks. This is a limited screening, not independent verification of source accuracy. GDP ratios, growth/inflation, gross enrollment and completion rates were not capped at 100; values over 100 can be meaningful.
- Unusual source values remain unchanged. Missing_Data_Profile.csv documents coverage per field. Reference_Discrepancies.csv records source conflicts (currently empty).
- Original full column names and values are preserved in Sustainability_Clean.csv; Sustainability_Joined.csv adds geography. FactIndicators includes all 154,489 expected indicator slots, including null observations, for honest coverage calculations.

## DAX measures for FactIndicators
```dax
Indicator Average = AVERAGE(FactIndicators[Value])
Observed Values = SUM(FactIndicators[HasValue])
Expected Values = COUNTROWS(FactIndicators)
Coverage % = DIVIDE([Observed Values], [Expected Values])
Selected Indicator Value =
IF(HASONEVALUE(DimIndicator[IndicatorKey]), [Indicator Average])
```
Format Coverage % as Percentage. Use a single-select indicator slicer and clearly label Indicator Average as an unweighted country mean. Never average unlike indicators together. Percentages and rates must not be summed. Country-weighted regional rates require the appropriate indicator-specific denominator; total population is not suitable for every rate. GDP, population and CO2 totals may be summed across countries for a single year, subject to coverage; summing across years answers a different question. Missing observations must be disclosed in every comparison.

## Suggested report pages
- Overview: single-year and indicator slicers, selected indicator mean, observed countries and coverage cards; country map and ranked country bar chart.
- Trends: line chart with Year, selected indicator value and a small set of countries. Use country slicers to avoid unreadable legends.
- Energy and environment: renewable energy %, electricity access %, and CO2 emissions trends; GDP per capita vs CO2 scatter for one year using FactCountryYear (look up indicator keys in DimIndicator).
- Inclusion: education, internet access, poverty and gender measures with coverage displayed; continent/UN region slicers.
- Data quality: missing-data profile and coverage by indicator/year. Do not mistake missing data for poor country performance.

GDP is current US$, CO2 is million tonnes; percentage values already use 0–100 units. Do not apply Power BI Percentage formatting directly to source percentage columns unless dividing by 100 first. Geography is the supplied static lookup, not a reconstruction of historical borders.

## Reproduce
Install pandas, numpy and openpyxl. Place the five original data files in a sibling raw/ folder and run `python prepare_data.py`. The script validates keys and joins and exports CSVs and Validation.json. Range_Review.csv is a separate snapshot screening described above. Source SHA-256 hashes in Validation.json identify the exact retrieved bytes. Requirements.txt lists dependencies. No PBIX report is included; the prepared tables and measures are ready for Power BI Desktop import.
