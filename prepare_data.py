from pathlib import Path
import pandas as pd, numpy as np, json, hashlib
ROOT=Path(__file__).resolve().parent
RAW=ROOT.parent/'raw'
OUT=ROOT
OUT.mkdir(exist_ok=True)
audit=[]
def load(name):
 p=RAW/name
 d=pd.read_csv(p) if p.suffix=='.csv' else pd.read_excel(p)
 d.columns=d.columns.str.strip()
 for c in d.select_dtypes('object'):
  d[c]=d[c].astype('string').str.strip().replace('',pd.NA)
 if 'Country Code' in d:d['Country Code']=d['Country Code'].str.upper()
 if 'Year' in d:d['Year']=pd.to_numeric(d['Year'],errors='raise').astype('Int64')
 return d
s=load('Sustainability Dataset.csv');original=s.copy();keys=['Country Code','Year']
assert not s.duplicated(keys).any() and s[keys].notna().all().all()
c=load('Country.xlsx');g=load('Continent.xlsx')
# Collapse repeated lookup records only if each non-null attribute is unambiguous.
for d in [c,g]:
 for col in d.columns.drop('Country Code'):
  assert d.groupby('Country Code')[col].nunique().max()<=1, f'Conflicting geography: {col}'
country=c.groupby('Country Code',as_index=False).first().merge(g.groupby('Country Code',as_index=False).first(),on='Country Code',validate='one_to_one')
assert len(country)==173
conflicts=[]
for file in ['Energy.xlsx','Electricity.xlsx']:
 d=load(file);assert not d.duplicated(keys).any()
 m=s.merge(d,on=keys,how='outer',suffixes=('','__reference'),validate='one_to_one',indicator=True)
 assert (m['_merge']=='both').all()
 for col in d.columns.drop(keys):
  a=m[col];b=m[col+'__reference'];same=np.isclose(a,b,rtol=1e-10,atol=1e-10,equal_nan=True)
  for idx in m.index[~same]:
   conflicts.append({'Country Code':m.at[idx,'Country Code'],'Year':m.at[idx,'Year'],'Indicator':col,'MainValue':a[idx],'ReferenceValue':b[idx],'Source':file,'Decision':'Retain main dataset; review source discrepancy'})
  # Only fill a missing main value from an explicit matching country-year reference.
  fill=a.isna() & b.notna();s.loc[fill,col]=b[fill].values
  audit.append({'Action':'Reference reconciliation','Source':file,'Column':col,'Rows':int(fill.sum()),'Disagreements':int((~same).sum())})
joined=s.merge(country,on='Country Code',how='left',validate='many_to_one',indicator=True)
assert len(joined)==len(original) and (joined['_merge']=='both').all();joined=joined.drop(columns='_merge')
# Short stable indicator keys retain a complete source-name dictionary.
cat=['Income Classification (World Bank Definition)','Regime Type (RoW Measure Definition)']
num=[x for x in s if x not in keys+cat]
dictionary=pd.DataFrame([{'IndicatorKey':f'I{i:02d}','SourceColumn':col,'DataType':'Decimal number','AggregationGuidance':'Use country-year value; average across countries only when explicitly labelled. GDP/population/CO2 totals can be summed for one year; do not sum rates or percentages.'} for i,col in enumerate(num,1)])
rename=dict(zip(dictionary.SourceColumn,dictionary.IndicatorKey))
fact=s.rename(columns=rename).rename(columns={cat[0]:'IncomeClassification',cat[1]:'RegimeType'})
long=fact.melt(id_vars=keys+['IncomeClassification','RegimeType'],value_vars=list(rename.values()),var_name='IndicatorKey',value_name='Value')
# Retain null rows so coverage measures have the full expected denominator.
long['HasValue']=long.Value.notna().astype(int)
year=pd.DataFrame({'Year':range(int(s.Year.min()),int(s.Year.max())+1)})
missing=pd.DataFrame({'Column':s.columns,'MissingCount':s.isna().sum().values,'MissingPercent':(100*s.isna().mean()).values})
conf=pd.DataFrame(conflicts,columns=['Country Code','Year','Indicator','MainValue','ReferenceValue','Source','Decision'])
for name,d in {'Sustainability_Clean':s,'Sustainability_Joined':joined,'FactCountryYear':fact,'FactIndicators':long,'DimCountry':country,'DimYear':year,'DimIndicator':dictionary,'Missing_Data_Profile':missing,'Reference_Discrepancies':conf,'Cleaning_Log':pd.DataFrame(audit)}.items():d.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig',float_format='%.15g')
summary={'source_rows':len(original),'output_rows':len(s),'countries':len(country),'year_min':int(s.Year.min()),'year_max':int(s.Year.max()),'indicators':len(num),'reference_discrepancies':len(conf),'missing_measurements':int(s[num].isna().sum().sum()),'duplicate_country_years':int(s.duplicated(keys).sum()),'unmatched_geography':int(joined['Country Name'].isna().sum()),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in RAW.iterdir()}}
(OUT/'Validation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
