import dask.dataframe as dd

# Correct dtypes (fix for Admin2 column)
dtypes = {
    'Admin2': 'object',
    'Confirmed': 'float64',
    'Deaths': 'float64',
    'Recovered': 'float64',
    'Latitude': 'float64',
    'Longitude': 'float64'
}

# URL to GitHub raw CSV (fixed with Accept-Encoding header)
url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/01-01-2021.csv"

# Read with FIXED storage_options
ddf = dd.read_csv(
    url,
    dtype=dtypes,
    storage_options={'headers': {'Accept-Encoding': 'identity'}}  ,
    blocksize="50KB",  # Force 2 chunks

)

# Compute total rows
total_rows = ddf.shape[0].compute()
print(f"Total rows: {total_rows}")