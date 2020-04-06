import pandas as pd
import numpy as np
import datetime as dt
import os
import logging

CSSE_DAILY_COL_FIPS='FIPS'
CSSE_DAILY_COL_PROVINCE_STATE='Province_State'
CSSE_DAILY_COL_COUNTRY_REGION='Country_Region'
CSSE_DAILY_COL_ADMIN2='Admin2'
CSSE_DAILY_COL_LATITUDE='Lat'
CSSE_DAILY_COL_LONGITUDE='Long_'
CSSE_DAILY_COL_CONFIRMED='Confirmed'
CSSE_DAILY_COL_DEATHS='Deaths'
CSSE_DAILY_COL_RECOVERED='Recovered'
CSSE_DAILY_COL_ACTIVE='Active'
CSSE_DAILY_COL_LOC_COMBINED='Combined_Key'
CSSE_DAILY_COL_HOVERTEXT='Hovertext'
CSSE_DAILY_COL_LAST_UPDATE='Last_Update'

CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION='Country/Region'
CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE='Province/State'
CSSE_TIMESERIES_COL_GLOBAL_LATITUDE='Lat'
CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE='Long'

CSSE_TIMESERIES_COL_USA_COUNTRY_REGION=CSSE_DAILY_COL_COUNTRY_REGION
CSSE_TIMESERIES_COL_USA_PROVINCE_STATE=CSSE_DAILY_COL_PROVINCE_STATE
CSSE_TIMESERIES_COL_USA_LATITUDE=CSSE_DAILY_COL_LATITUDE
CSSE_TIMESERIES_COL_USA_LONGITUDE=CSSE_DAILY_COL_LONGITUDE
CSSE_TIMESERIES_COL_USA_UID='UID'
CSSE_TIMESERIES_COL_USA_ISO2='iso2'
CSSE_TIMESERIES_COL_USA_ISO2='iso3'
CSSE_TIMESERIES_COL_USA_CODE3='code3'
CSSE_TIMESERIES_COL_USA_FIPS='FIPS'

today_str = f'{dt.datetime.today():%m-%d-%Y}'
yesterday_str = f'{dt.datetime.today() - dt.timedelta(days=1):%m-%d-%Y}'

csse_base_url = './covid-19-data/csse_covid_19_data/'
csse_daily_url = csse_base_url + 'csse_covid_19_daily_reports/'
csse_timeseries_url = csse_base_url + 'csse_covid_19_time_series/'


def get_location(row):
    if CSSE_DAILY_COL_LOC_COMBINED in row.index:
        return row[CSSE_DAILY_COL_LOC_COMBINED]
    if CSSE_DAILY_COL_PROVINCE_STATE in row.index:
        if CSSE_DAILY_COL_COUNTRY_REGION in row.index:
            return row[CSSE_DAILY_COL_PROVINCE_STATE] + ', ' + row[CSSE_DAILY_COL_COUNTRY_REGION]
        else:
            return row[CSSE_DAILY_COL_PROVINCE_STATE]
    return row.name


def get_hovertext(row):
    return get_location(row) + '<br>' + \
           'Confirmed = ' + str(row[CSSE_DAILY_COL_CONFIRMED]) + '<br>' + \
           'Deaths = ' + str(row[CSSE_DAILY_COL_DEATHS]) + '<br>' + \
           'Recovered =' + str(row[CSSE_DAILY_COL_RECOVERED]) + '<br>' + \
           'Active =' + str(row[CSSE_DAILY_COL_ACTIVE])


add_hovertext = lambda df: df.apply(lambda row: get_hovertext(row), axis=1)

class CovidDataProcessor:
    rename_countries = {
        'US': 'United States of America',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo',
        'Korea, South': 'South Korea'
    }
    daily_aggregation_functions = {
        CSSE_DAILY_COL_CONFIRMED: 'sum',
        CSSE_DAILY_COL_DEATHS: 'sum',
        CSSE_DAILY_COL_RECOVERED: 'sum',
        CSSE_DAILY_COL_ACTIVE: 'sum',
        CSSE_DAILY_COL_LATITUDE: 'mean',
        CSSE_DAILY_COL_LONGITUDE: 'mean',
        CSSE_DAILY_COL_LAST_UPDATE: 'max'
    }

    def __init_logger(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        #log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.logger.setLevel(logging.INFO)

    def __read_csse_daily_report(self):
        csse_daily_csv = csse_daily_url + today_str + '.csv'
        if not os.path.isfile(csse_daily_csv):
            csse_daily_csv = csse_daily_url + yesterday_str + '.csv'
        self.logger.info('Reading f{csse_daily_csv}...')
        df_daily_global = pd.read_csv(csse_daily_csv, dtype={CSSE_DAILY_COL_FIPS: str})

        # make a world countries data frame
        self.logger.info('processing daily global data...')
        self.df_daily_countries = df_daily_global.drop(
            columns=[CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_PROVINCE_STATE, CSSE_DAILY_COL_ADMIN2, CSSE_DAILY_COL_LOC_COMBINED])
        self.df_daily_countries = self.df_daily_countries.groupby(
            self.df_daily_countries[CSSE_DAILY_COL_COUNTRY_REGION]).aggregate(self.daily_aggregation_functions)
        self.df_daily_countries.rename(self.rename_countries, inplace=True)
        self.df_daily_countries[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_countries)

        # compute global totals
        self.logger.info('computing global daily sums...')
        self.global_totals = self.df_daily_countries.aggregate(self.daily_aggregation_functions)

        # make a US counties dataframe
        self.logger.info('Deriving data for US counties...')
        self.df_daily_us_counties = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        # drop rows with NaN in FIPS column
        self.df_daily_us_counties = self.df_daily_us_counties[self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].notna()]
        self.df_daily_us_counties[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_countries)


    def __read_csse_time_series_reports(self):
        csse_timeseries_confirmed_global_csv = csse_timeseries_url + 'time_series_covid19_confirmed_global.csv'
        csse_timeseries_deaths_global_csv = csse_timeseries_url + 'time_series_covid19_deaths_global.csv'
        csse_timeseries_recovered_global_csv = csse_timeseries_url + 'time_series_covid19_recovered_global.csv'

        csse_timeseries_confirmed_usa_csv = csse_timeseries_url + 'time_series_covid19_confirmed_US.csv'
        csse_timeseries_deaths_usa_csv = csse_timeseries_url + 'time_series_covid19_deaths_US.csv'

        self.logger.info(f'Reading global time series confirmed cases data from {csse_timeseries_confirmed_global_csv}...')
        self.df_time_series_confirmed_countries = pd.read_csv(csse_timeseries_confirmed_global_csv)
        self.logger.info(f'Reading  global time series deaths data from {csse_timeseries_deaths_global_csv}...')
        self.df_time_series_deaths_countries = pd.read_csv(csse_timeseries_deaths_global_csv)
        self.logger.info(f'Reading  global time series recovered cases data from {csse_timeseries_recovered_global_csv}...')
        self.df_time_series_recovered_countries = pd.read_csv(csse_timeseries_recovered_global_csv)

        self.logger.info('Cleaning up global time series data...')
        drop_columns_global = lambda df: df.drop(
            columns=[CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE, CSSE_TIMESERIES_COL_GLOBAL_LATITUDE, CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE],
            inplace=True
        )

        # drop unneeded columns
        drop_columns_global(self.df_time_series_confirmed_countries)
        drop_columns_global(self.df_time_series_deaths_countries)
        drop_columns_global(self.df_time_series_recovered_countries)

        aggregate_sums_global = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION]).aggregate('sum')

        # aggregate rows belonging to the same country
        self.df_time_series_confirmed_countries = aggregate_sums_global(self.df_time_series_confirmed_countries)
        self.df_time_series_deaths_countries = aggregate_sums_global(self.df_time_series_deaths_countries)
        self.df_time_series_recovered_countries = aggregate_sums_global(self.df_time_series_recovered_countries)

        self.time_series_confirmed_global =  self.df_time_series_confirmed_countries.aggregate('sum')
        self.time_series_deaths_global =  self.df_time_series_deaths_countries.aggregate('sum')
        self.time_series_recovered_global =  self.df_time_series_recovered_countries.aggregate('sum')

        # rename non-conformant country names
        self.df_time_series_confirmed_countries.rename(self.rename_countries, inplace=True)
        self.df_time_series_deaths_countries.rename(self.rename_countries, inplace=True)
        self.df_time_series_recovered_countries.rename(self.rename_countries, inplace=True)

        self.logger.info(f'Reading US time series confirmed cases data from {csse_timeseries_confirmed_usa_csv}...')
        self.df_time_series_confirmed_us_counties = pd.read_csv(csse_timeseries_confirmed_usa_csv)
        self.logger.info(f'Reading  global time series deaths data from {csse_timeseries_deaths_usa_csv}...')
        self.df_time_series_deaths_us_counties = pd.read_csv(csse_timeseries_deaths_usa_csv)

        self.logger.info('Cleaning up US time series data...')
        drop_columns_usa = lambda df: df.drop(
            columns=[
                CSSE_TIMESERIES_COL_USA_COUNTRY_REGION,
                CSSE_TIMESERIES_COL_USA_LATITUDE,
                CSSE_TIMESERIES_COL_USA_LONGITUDE,
                CSSE_TIMESERIES_COL_USA_UID,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_CODE3,
                CSSE_TIMESERIES_COL_USA_FIPS,
            ],
            inplace=True
        )

        # drop unneeded columns
        drop_columns_usa(self.df_time_series_confirmed_us_counties)
        drop_columns_usa(self.df_time_series_deaths_us_counties)

        aggregate_sums_states = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_USA_PROVINCE_STATE]).aggregate('sum')
        self.df_time_series_confirmed_us_states = aggregate_sums_states(self.df_time_series_confirmed_us_counties)
        self.df_time_series_deaths_us_states = aggregate_sums_states(self.df_time_series_deaths_us_counties)

    def __init__(self, *args, **kwargs):
        self.__init_logger()
        self.__read_csse_daily_report()
        self.__read_csse_time_series_reports()
        pass





