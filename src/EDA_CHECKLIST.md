# Exploratory Data Analysis (EDA) Checklist

A step-by-step EDA workflow distilled from Rob Mulla's "EDA with Python and Pandas" tutorial.

---

## 0. Imports & Setup
- [ ] Import core libraries: `pandas as pd`, `numpy as np`
- [ ] Import visualization libraries: `matplotlib.pylab as plt`, `seaborn as sns`
- [ ] Set a plot style sheet, e.g. `plt.style.use('ggplot')`
- [ ] Expand displayed columns: `pd.set_option('display.max_columns', 200)`
- [ ] Read the data: `df = pd.read_csv('...')`

---

## 1. Data Understanding
Get a high-level feel for the shape and contents before touching anything.
- [ ] `df.shape` — how many rows and columns
- [ ] `df.head()` — preview first 5 rows (adjust count as needed)
- [ ] `df.columns` — list out all column names
- [ ] `df.dtypes` — check the data type of each column (object/float/int/etc.)
- [ ] `df.describe()` — summary statistics for numeric columns (count, mean, min, max, quartiles)

---

## 2. Data Preparation (Cleaning)
Drop what you don't need *first*, so you don't waste effort cleaning unused columns.

### Subset columns
- [ ] Decide which columns to keep vs. drop (comment out unwanted ones from the `df.columns` list)
- [ ] Subset by list: `df = df[['col1', 'col2', ...]].copy()` (use `.copy()` to avoid reference issues)
- [ ] Alternative: drop columns with `df.drop(['col'], axis=1)`

### Fix data types
- [ ] Convert date columns: `pd.to_datetime(df['date_col'])`
- [ ] Convert numeric columns: `pd.to_numeric(df['col'])`

### Rename columns
- [ ] Standardize names (consistent casing, no spaces): `df.rename(columns={'old': 'New'})`

### Missing values
- [ ] `df.isna().sum()` — count nulls per column

### Duplicates
- [ ] `df.duplicated()` — flag duplicate rows
- [ ] `df.loc[df.duplicated()]` — inspect duplicated rows
- [ ] Check duplicates on a subset: `df.duplicated(subset=['col'])`
- [ ] Inspect a specific case with `df.query("col == 'value'")` to understand *why* duplicates exist
- [ ] Remove duplicates using the inverse mask on key columns:
      `df = df.loc[~df.duplicated(subset=['name', 'location', 'date'])]`
- [ ] Reset index after dropping rows: `df.reset_index(drop=True)`

---

## 3. Feature Understanding (Univariate Analysis)
Look at each feature individually — distributions and outliers.
- [ ] `df['col'].value_counts()` — frequency of each value (sorted most → least)
- [ ] Bar plot of top values: `df['col'].value_counts().head(10).plot(kind='barh')`
- [ ] Always add titles and axis labels (`ax.set_xlabel()`, `ax.set_ylabel()`)
- [ ] Histogram for continuous values: `df['col'].plot(kind='hist', bins=20)`
- [ ] Try different bin sizes to clarify the distribution
- [ ] Density plot (KDE): `df['col'].plot(kind='kde')` — normalized, cleaner for comparisons

---

## 4. Feature Relationships (Bivariate / Multivariate Analysis)
Examine how features relate to one another.
- [ ] Scatter plot of two features: `df.plot(kind='scatter', x='col1', y='col2')`
- [ ] Use `plt.show()` to suppress the matplotlib object printout
- [ ] Seaborn scatter with a color dimension (hue):
      `sns.scatterplot(x='col1', y='col2', hue='col3', data=df)`
- [ ] Pair plot to compare many features at once:
      `sns.pairplot(df, vars=[...], hue='category_col')`
- [ ] Correlation matrix on numeric columns: `df[num_cols].dropna().corr()`
- [ ] Correlation heatmap: `sns.heatmap(df_corr, annot=True)`

---

## 5. Ask a Question About the Data
Use everything learned to answer a concrete question.
- [ ] Frame a clear question (e.g. *"Which locations have the fastest coasters, min 10 coasters?"*)
- [ ] Filter out invalid/placeholder values: `df.query("location != 'Other'")`
- [ ] Group by a dimension: `.groupby('location')`
- [ ] Aggregate with multiple stats: `['col'].agg(['mean', 'count'])`
- [ ] Filter the aggregated result: `.query("count >= 10")`
- [ ] Sort the results: `.sort_values('mean')`
- [ ] Visualize the answer with a labeled plot (`kind='barh'`, title, axis labels)

---

### Guiding principles
- Drop unwanted columns/rows **before** cleaning to save effort.
- Always use `.copy()` when creating a working subset.
- Always label plots (title + axis labels).
- Verify and correct dtypes early.
- Asking a real question forces you to learn the pandas tools you need.
