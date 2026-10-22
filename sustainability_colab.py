# %% [markdown]
# Sustainability dataset: exploration and conservative cleaning
# In Google Colab: upload this script through File > Upload notebook (select
# the .ipynb version if available), or paste this entire script into a code cell.
# Run it, then select Sustainability Dataset(1).csv when prompted.
# No installation is required in Colab. Outputs are written to a new run folder.
# Missing values are NOT imputed; records and numeric precision are preserved.

# %% 1. Imports and file upload
from pathlib import Path
from io import BytesIO
import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    from IPython.display import display
except ImportError:  # Local command-line testing
    display = print

# Set a local path for testing outside Colab; leave as None in Colab.
INPUT_PATH = None
DOWNLOAD_RESULTS = True


def main(input_path=None, download=True):
    if input_path is None:
        from google.colab import files
        uploaded = files.upload()
        if len(uploaded) != 1:
            raise ValueError('Please upload exactly one CSV file.')
        filename, source_bytes = next(iter(uploaded.items()))
    else:
        filename = Path(input_path).name
        source_bytes = Path(input_path).read_bytes()

    # Explicit encoding: fail rather than silently replacing unknown characters.
    source_text = source_bytes.decode('utf-8-sig')
    records = list(csv.reader(source_text.splitlines(keepends=True)))
    if not records:
        raise ValueError('The CSV is empty.')
    headers = records[0]
    if len(headers) != len(set(headers)):
        raise ValueError('Duplicate source headers: resolve explicitly before cleaning.')
    if any(len(row) != len(headers) for row in records[1:]):
        raise ValueError('Malformed/blank CSV record: inspect source; no rows were skipped.')

    # String import prevents automatic loss of leading zeros or literal NA labels.
    raw = pd.read_csv(BytesIO(source_bytes), dtype='string',
                      keep_default_na=False, na_filter=False, encoding='utf-8-sig',
                      skip_blank_lines=False)
    original = raw.copy(deep=True)
    out = Path('sustainability_outputs_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(exist_ok=False)
    (out / 'original_source.csv').write_bytes(source_bytes)
    print('Source:', filename, '| SHA256:', hashlib.sha256(source_bytes).hexdigest())

    # %% 2. Explore BEFORE cleaning
    print('\nSOURCE STRUCTURE:', raw.shape)
    display(raw.head(10))
    print('Imported as strings intentionally. Inferred analytical types appear below.')
    missing = raw.apply(lambda s: s.str.strip().eq(''))
    profile = pd.DataFrame({
        'source_dtype': raw.dtypes.astype(str),
        'blank_cells': missing.sum(),
        'blank_pct': (missing.mean() * 100).round(2),
        'distinct_nonblank': raw.mask(missing).nunique(),
    })
    display(profile.sort_values('blank_pct', ascending=False))
    profile.to_csv(out / 'source_profile.csv', index_label='column')
    print('Exact duplicate records:', int(raw.duplicated().sum()))

    # %% 3. Conservative cleaning with cell-level audit
    clean = raw.copy(deep=True)
    audit = []
    flags = []

    def flag(mask, column, rule, values=None):
        for i in clean.index[pd.Series(mask, index=clean.index).fillna(False)]:
            flags.append({'source_record': int(i) + 1, 'column': column,
                          'rule': rule, 'value': str(clean.at[i, column] if values is None else values.loc[i])})

    for c in clean:
        before = clean[c].copy()
        after = before.str.strip().replace('', pd.NA)
        changed = before.ne(after).fillna(True) & ~(before.isna() & after.isna())
        for i in clean.index[changed]:
            audit.append({'source_record': int(i) + 1, 'column': c,
                          'before': before.loc[i],
                          'after': None if pd.isna(after.loc[i]) else after.loc[i],
                          'reason': 'Blank to missing' if pd.isna(after.loc[i]) else 'Trim outer whitespace'})
        clean[c] = after

    keys = ['Country Code', 'Year']
    categories = ['Country Code', 'Income Classification (World Bank Definition)',
                  'Regime Type (RoW Measure Definition)']
    required = keys + categories[1:]
    if not set(required).issubset(clean.columns):
        raise ValueError('Required columns missing. This script targets the supplied dataset.')

    # No guessed placeholder list: literal NA, NULL, .. etc. remain visible and flagged.
    numeric_columns = [c for c in clean if c not in categories]
    type_log = []
    for c in numeric_columns:
        parsed = pd.to_numeric(clean[c], errors='coerce')
        invalid = clean[c].notna() & parsed.isna()
        flag(invalid, c, 'Unparseable numeric text; column kept as strings')
        nonfinite = parsed.notna() & ~np.isfinite(parsed.astype(float))
        flag(nonfinite, c, 'Non-finite numeric value; retained for review')
        if not invalid.any():
            if c == 'Year':
                fractional = parsed.notna() & parsed.mod(1).ne(0)
                flag(fractional, c, 'Year is not a whole number')
                if not fractional.any() and not nonfinite.any():
                    clean[c] = parsed.astype('Int64')
                else:
                    clean[c] = parsed
            else:
                clean[c] = parsed  # no rounding, scaling, interpolation or winsorisation
        type_log.append({'column': c, 'output_dtype': str(clean[c].dtype),
                         'parse_failures': int(invalid.sum())})

    flag(clean['Country Code'].notna() & ~clean['Country Code'].str.fullmatch(r'[A-Z]{3}', na=False),
         'Country Code', 'Expected three uppercase letters; no code inferred/corrected')
    for c in keys:
        flag(clean[c].isna(), c, 'Missing country-year key')
    duplicate_key = clean.duplicated(keys, keep=False)
    flag(duplicate_key, 'Country Code', 'Repeated country-year key; all records retained')
    clean.loc[duplicate_key].to_csv(out / 'duplicate_key_review.csv', index=False)
    exact_duplicates = clean.duplicated(keep=False)
    clean.loc[exact_duplicates].to_csv(out / 'duplicate_record_review.csv', index=False)

    # Only indicators with genuine percentage-share/scale bounds get 0..100 checks.
    # GDP ratios, growth rates, gross enrolment and completion rates are excluded.
    bounded_fragments = [
        'EG.ELC.ACCS.ZS', 'SE.PRM.UNER.ZS', 'SG.GEN.PARL.ZS', 'EG.ELC.RNEW.ZS',
        'EG.FEC.RNEW.ZS', 'SG.LAW.INDX', 'SN_ITK_DEFC', 'SI_POV_DAY1',
        'IT_MOB_2GNTWK', 'IT_MOB_3GNTWK', 'SP_ACS_BSRVH2O', 'SL_TLF_UEM',
        'SI.POV.GINI', 'IT.NET.USER.ZS', 'SP.RUR.TOTL.ZS', 'SP.URB.TOTL.IN.ZS',
    ]
    for c in numeric_columns:
        s = pd.to_numeric(clean[c], errors='coerce')
        if any(fragment in c for fragment in bounded_fragments):
            flag(s.notna() & ~s.between(0, 100), c, 'Outside expected 0..100; review only')
        # IQR identifies unusual observations, not necessarily errors in a cross-country panel.
        finite = s[np.isfinite(s.astype(float))].dropna()
        if c != 'Year' and len(finite) >= 4:
            q1, q3 = finite.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr > 0:
                flag(s.notna() & ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)),
                     c, 'IQR outlier; descriptive flag only, retained')

    rural = next(c for c in clean if 'SP.RUR.TOTL.ZS' in c)
    urban = next(c for c in clean if 'SP.URB.TOTL.IN.ZS' in c)
    total = pd.to_numeric(clean[rural], errors='coerce') + pd.to_numeric(clean[urban], errors='coerce')
    flag(total.notna() & (total - 100).abs().gt(0.5), rural,
         'Rural + urban differs from 100 by more than 0.5 percentage points')

    # %% 4. Describe analytical data and visualise coverage
    print('\nANALYTICAL TYPES')
    clean.info()
    display(clean.describe(include='all').T)
    clean.describe(include='all').T.to_csv(out / 'descriptive_statistics.csv', index_label='column')
    display(clean[categories].apply(lambda s: s.value_counts()).fillna(0))
    for c in categories:
        print('\nCategory counts:', c)
        display(clean[c].value_counts(dropna=False).to_frame('records'))
    print('Country codes:', clean['Country Code'].nunique(),
          '| Year range:', clean['Year'].min(), 'to', clean['Year'].max())
    print('Records by year:')
    display(clean.groupby('Year', dropna=False).size().to_frame('records'))
    coverage = clean.groupby('Country Code', dropna=False)['Year'].agg(['count', 'nunique', 'min', 'max'])
    coverage.to_csv(out / 'country_year_coverage.csv')
    clean.isna().mean().mul(100).sort_values().tail(15).plot.barh(figsize=(11, 7))
    plt.xlabel('Missing values (%)'); plt.title('15 indicators with highest missingness')
    plt.tight_layout(); plt.savefig(out / 'missingness.png', dpi=150); plt.show()

    # %% 5. Integrity checks and export
    pd.testing.assert_frame_equal(raw, original)
    assert clean.shape == raw.shape, 'Rows or columns unexpectedly changed'
    assert clean.index.equals(raw.index), 'Source record order changed'
    assert list(clean.columns) == list(raw.columns), 'Column names/order changed'
    for c in numeric_columns:
        expected = pd.to_numeric(raw[c].str.strip().replace('', pd.NA), errors='coerce')
        actual = pd.to_numeric(clean[c], errors='coerce')
        pd.testing.assert_series_equal(expected, actual, check_dtype=False)
    audit_df = pd.DataFrame(audit, columns=['source_record', 'column', 'before', 'after', 'reason'])
    flag_df = pd.DataFrame(flags, columns=['source_record', 'column', 'rule', 'value'])
    audit_df.to_csv(out / 'cleaning_audit.csv', index=False)
    flag_df.to_csv(out / 'quality_flags.csv', index=False)
    pd.DataFrame(type_log).to_csv(out / 'type_conversion_log.csv', index=False)
    clean.to_csv(out / 'sustainability_cleaned.csv', index=False)
    summary = {
        'source_file': filename, 'sha256': hashlib.sha256(source_bytes).hexdigest(),
        'rows_before': len(raw), 'rows_after': len(clean), 'columns': len(clean.columns),
        'country_codes': int(clean['Country Code'].nunique()),
        'missing_cells': int(clean.isna().sum().sum()), 'edited_cells': len(audit),
        'duplicate_key_records': int(duplicate_key.sum()), 'quality_flags': len(flags),
        'integrity_checks': 'passed',
        'policy': 'No rows dropped; no imputation; no rounding; no outlier removal; original bytes preserved.',
        'limitations': 'Source definitions and country-code membership not externally validated. '
                       'CSV does not store dtypes; use type_conversion_log when reloading. '
                       'Source record is 1-based data-record position, excluding header. '
                       'Missing data must be considered before comparing country/year averages.',
    }
    (out / 'run_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('\nRUN SUMMARY'); display(pd.Series(summary))
    print('Quality flags by rule:'); display(flag_df['rule'].value_counts())
    archive = out.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.iterdir()):
            z.write(path, arcname=path.name)
    print('Results:', archive.resolve())
    if input_path is None and download:
        from google.colab import files
        files.download(str(archive))
    return raw, clean, audit_df, flag_df, out


if __name__ == '__main__':
    results = main(INPUT_PATH, DOWNLOAD_RESULTS)
