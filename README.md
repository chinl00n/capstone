Sustainability Dataset
<p align="center">
  <img src="https://img.shields.io/badge/Focus-Sustainable%20Development-2E8B57" alt="Sustainable Development" />
  <img src="https://img.shields.io/badge/Period-2000--2018-blue" alt="Period 2000–2018" />
  <img src="https://img.shields.io/badge/Countries-173-orange" alt="173 countries" />
</p>

<h1 align="center">Global Sustainability Dataset</h1>

This repository contains a country-year dataset for analysing economic development, environmental sustainability, energy access, and social well-being across 173 countries from 2000 to 2018. It combines economic, environmental, demographic, education, and development indicators with geographic and energy reference tables.
The dataset supports exploratory data analysis (EDA), sustainability benchmarking, panel-data research, data visualisation, and missing-data assessment. It is historical and should not be interpreted as representing current country conditions.
Project focus: Explore how economic prosperity relates to environmental performance, electricity access, and inclusive development. Statistical associations do not, by themselves, establish causation.

📋 Dataset Overview
File	Rows	Columns	Description
Sustainability Dataset.csv	3,287	51	Main country-year dataset of sustainability and development indicators
Country.xlsx	3,287	2	Country names and country codes; repeated across years
Continent.xlsx	3,287	3	Continent and UN SDG world-region classifications; repeated across years
Energy.xlsx	3,287	4	Renewable energy consumption and annual CO₂ emissions by country-year
Electricity.xlsx	3,287	3	Electricity access by country-year


- Time horizon: 2000–2018 inclusive (19 years)
- Geographic coverage: 173 countries
- Unit of analysis: Country-year
- Main identifiers: Country Code, Year
- Total country-year observations: 3,287
- Main themes: Economy, environment, energy, education, poverty, inequality, connectivity, and population
The main dataset includes many of the energy and electricity indicators found in the supplementary files. Avoid duplicating equivalent columns during joins.
🗂️ Data Dictionary
The main CSV has 51 columns. The table below highlights the principal fields used for analysis; the full original column names include indicator descriptions and source codes.
Indicator / field	Type	Description
Country Code	String	Three-letter country identifier
Year	Integer	Observation year (2000–2018)
GDP (current US$) - NY.GDP.MKTP.CD	Numeric	Gross domestic product in current US dollars
GDP per capita (current US$) - NY.GDP.PCAP.CD	Numeric	GDP per person in current US dollars
Annual production-based emissions of carbon dioxide (CO2), measured in million tonnes	Numeric	Annual production-based CO₂ emissions, million tonnes
Renewable energy consumption (% of total final energy consumption) - EG.FEC.RNEW.ZS	Numeric	Renewable share of final energy consumption, percent
Renewable electricity output (% of total electricity output) - EG.ELC.RNEW.ZS	Numeric	Renewable share of electricity generation, percent
Access to electricity (% of population) - EG.ELC.ACCS.ZS	Numeric	Population with access to electricity, percent
Income Classification (World Bank Definition)	Category	Country income grouping
Life expectancy at birth, total (years) - SP.DYN.LE00.IN	Numeric	Expected lifespan at birth, years
Gini index (World Bank estimate) - SI.POV.GINI	Numeric	Measure of income inequality
Proportion of population below international poverty line (%) - SI_POV_DAY1 - 1.1.1	Numeric	Population below the specified international poverty line, percent
Primary completion rate, total (% of relevant age group) - SE.PRM.CMPT.ZS	Numeric	Primary education completion rate
Proportion of population using basic drinking water services (%) - SP_ACS_BSRVH2O - 1.4.1	Numeric	Access to basic drinking water, percent
Population, total - SP.POP.TOTL	Numeric	Total population
Country Name	String	Country name in Country.xlsx
Continent	Category	Continent in Continent.xlsx
World Regions (UN SDG Definition)	Category	UN SDG geographic grouping in Continent.xlsx


Note: Percentages and their stored units should be verified before calculating derived indicators. For instance, a value of 25 for a percentage indicator means 25%, not 0.25%.
🔍 Data Quality & Cleaning Notes
The files contain a complete set of 173 × 19 = 3,287 country-year keys, but many individual indicator values are missing.
Indicator	Missing records	Missing share
Gini index	1,984	60.4%
International poverty-line measure	1,983	60.3%
3G mobile network coverage	1,930	58.7%
Women's unemployment rate	1,481	45.1%
Men's unemployment rate	1,480	45.0%


Key cleaning considerations:
- Missing data: Assess missingness by country, region, year, and indicator before choosing complete-case analysis or imputation. Do not replace all missing values with zero.
- Country and continent lookup tables: Each contains repeated country codes. Deduplicate only after confirming each code maps consistently to one country name or region.
- Join keys: Use Country Code + Year for Energy.xlsx and Electricity.xlsx; use a validated, unique Country Code lookup for country and continent metadata.
- Overlapping columns: Some indicators appear in both the main CSV and supplementary files. Reconcile values and choose an authoritative source instead of creating duplicate measures.
- Units: CO₂ is reported in million tonnes and GDP in current US dollars. Conversions are necessary when calculating emissions intensity.
- Historical and observational data: Changes in nominal GDP may reflect inflation or exchange rates; correlation alone cannot establish causal effects.
🎯 Research Problem Statements
1. Economic Growth vs Environmental Sustainability
Problem: To what extent is economic development associated with carbon emissions and renewable energy adoption across countries, and how do these relationships vary by income group and region?
Possible analyses: GDP per capita versus emissions, renewable energy trends, carbon intensity, and country-level decoupling patterns.
2. Energy Accessibility and Renewable Energy Transition
Problem: How does electricity access relate to renewable energy consumption and economic development, and which countries face the greatest gaps in access and sustainable energy transition?
Possible analyses: Electricity access by region, renewable energy share by income group, trend analysis, and country clustering.
3. Economic Inequality and Sustainable Human Development
Problem: How are income inequality, poverty, and economic prosperity associated with life expectancy, education, and access to basic drinking water?
Possible analyses: GDP per capita versus life expectancy, inequality and poverty comparisons, and income-group benchmarking. The high missingness of inequality and poverty measures must be explicitly addressed.
🛠️ Usage Example (Python & Pandas)
Place all five files in the same folder as the notebook or upload them to Google Colab.
import pandas as pd

# Read source files
sustainability = pd.read_csv('Sustainability Dataset.csv')
country = pd.read_excel('Country.xlsx')
continent = pd.read_excel('Continent.xlsx')
energy = pd.read_excel('Energy.xlsx')
electricity = pd.read_excel('Electricity.xlsx')

# Validate unique country-year records
key = ['Country Code', 'Year']
assert not sustainability.duplicated(key).any()
assert not energy.duplicated(key).any()
assert not electricity.duplicated(key).any()

# Check lookup consistency before deduplicating
for lookup in [country, continent]:
    for column in lookup.columns.drop('Country Code'):
        assert lookup.groupby('Country Code')[column].nunique(dropna=False).max() <= 1, column

country_lookup = country.drop_duplicates('Country Code')
continent_lookup = continent.drop_duplicates('Country Code')

# Attach geographic metadata without multiplying country-year rows
df = sustainability.merge(country_lookup, on='Country Code', how='left', validate='many_to_one')
df = df.merge(continent_lookup, on='Country Code', how='left', validate='many_to_one')
assert len(df) == len(sustainability)

# Supplementary energy/electricity data are already represented in the main
# dataset; inspect and reconcile them before deciding whether to merge.

# Report missing values
missing = df.isna().mean().mul(100).sort_values(ascending=False)
print('Missing data (%):')
print(missing.head(10).round(1))

# Compare median GDP per capita by continent
metric = 'GDP per capita (current US$) - NY.GDP.PCAP.CD'
comparison = df.groupby('Continent')[metric].median().sort_values(ascending=False)
print('\nMedian country-year GDP per capita by continent:')
print(comparison.round(2))
Example: Economic Development and CO₂ Emissions
import matplotlib.pyplot as plt

emissions = 'Annual production-based emissions of carbon dioxide (CO2), measured in million tonnes'
gdp_pc = 'GDP per capita (current US$) - NY.GDP.PCAP.CD'

subset = df[[gdp_pc, emissions]].dropna()
subset = subset[(subset[gdp_pc] > 0) & (subset[emissions] >= 0)]

plt.figure(figsize=(9, 5))
plt.scatter(subset[gdp_pc], subset[emissions], alpha=0.25)
plt.xscale('log')
plt.xlabel('GDP per capita (current US$, log scale)')
plt.ylabel('Annual CO₂ emissions (million tonnes)')
plt.title('GDP per Capita vs Total CO₂ Emissions, 2000–2018')
plt.tight_layout()
plt.show()
Interpretation caution: Total emissions are strongly influenced by population size. Consider per-capita emissions and GDP-based intensity, and account for country and year effects before drawing conclusions.
📊 Suggested Project Outputs
1. Data quality and missingness report
2. Cleaned country-year analytical dataset and data dictionary
3. EDA notebook with regional and time-series visualisations
4. Statistical analysis of the three research problems
5. Power BI or Python dashboard
6. Executive summary, limitations, and evidence-based recommendations
📁 Suggested Repository Structure
sustainability-analysis/
├── README.md
├── data/
│   ├── Sustainability Dataset.csv
│   ├── Country.xlsx
│   ├── Continent.xlsx
│   ├── Energy.xlsx
│   └── Electricity.xlsx
├── notebooks/
│   └── sustainability_eda.ipynb
├── outputs/
│   └── figures/
└── requirements.txt
📚 Data Provenance and Limitations
The dataset uses indicator labels and codes associated with sources such as the World Bank and UN SDG framework. The original extraction dates, licences, and full source provenance have not been independently verified. Confirm the underlying sources and reuse permissions before public redistribution or formal publication.
🧰 Tools
- Python, Pandas, Matplotlib
- Jupyter Notebook / Google Colab
- Power BI (optional)
- Statistical modelling packages such as statsmodels (optional)
📓 Notebook
Add your sustainability notebook link here after uploading it to Google Colab:
[Open in Google Colab](YOUR_COLAB_NOTEBOOK_URL)
Project: Sustainability Data Analytics Capstone
Study period: 2000–2018
Unit of analysis: Country-year
