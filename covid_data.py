import pandas as pd
import numpy as np
import datetime as dt
import os
import logging

SCOPE_WORLD='Worldwide'
SCOPE_USA='United States'

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
        self.df_daily_countries.rename(self.rename_countries, inplace=True)
        self.df_daily_countries = self.df_daily_countries.groupby(
            self.df_daily_countries[CSSE_DAILY_COL_COUNTRY_REGION]).aggregate(self.daily_aggregation_functions)
        self.df_daily_countries[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_countries)

        # compute global totals
        self.logger.info('computing global daily totals...')
        self.global_totals = self.df_daily_countries.aggregate(self.daily_aggregation_functions)

        # make a US counties dataframe
        self.logger.info('Deriving data for US counties...')
        self.df_daily_us_counties = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        # drop rows with NaN in FIPS column
        self.df_daily_us_counties = self.df_daily_us_counties[self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].notna()]
        self.df_daily_us_counties[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_countries)

        # compute us totals
        self.logger.info('computing US daily totals...')
        self.usa_totals = self.df_daily_us_counties.aggregate(self.daily_aggregation_functions)

    def __get_csse_time_series_data(self, url, sum_index='Total', dropcolumns_func=None, aggregate_func=None, logtext=None, rename_countries=False):
        if logtext is not None:
            self.logger.info(f'Reading {logtext} data from {url}...')
        df = pd.read_csv(url)

        if dropcolumns_func is not None:
            self.logger.info(f'Dropping unwanted columns...')
            dropcolumns_func(df)
        if aggregate_func is not None:
            df = aggregate_func(df)
        if rename_countries:
            df.rename(index=self.rename_countries, inplace=True)
            df.sort_index(inplace=True)
        sum = df.aggregate('sum')
        df_sum = pd.DataFrame([sum], index=[sum_index])
        df = pd.concat([df_sum, df])
        return df, sum

    def __read_csse_time_series_reports(self):
        drop_columns_global = lambda df: df.drop(
            columns=[
                CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE,
                CSSE_TIMESERIES_COL_GLOBAL_LATITUDE,
                CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE],
            inplace=True
        )

        aggregate_sums_global = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION]).aggregate('sum')

        csse_timeseries_confirmed_global_csv = csse_timeseries_url + 'time_series_covid19_confirmed_global.csv'
        csse_timeseries_deaths_global_csv = csse_timeseries_url + 'time_series_covid19_deaths_global.csv'
        csse_timeseries_recovered_global_csv = csse_timeseries_url + 'time_series_covid19_recovered_global.csv'

        self.df_confirmed_by_date_world, self.confirmed_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_confirmed_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series confirmed cases',
                rename_countries=True,
                sum_index='Worldwide'
            )
        self.df_deaths_by_date_world, self.deaths_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_deaths_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series deaths',
                rename_countries=True,
                sum_index = 'Worldwide'
        )
        self.df_recovered_by_date_world, self.recovered_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_recovered_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series recovered cases',
                rename_countries=True,
                sum_index = 'Worldwide'
        )


        csse_timeseries_confirmed_usa_csv = csse_timeseries_url + 'time_series_covid19_confirmed_US.csv'
        csse_timeseries_deaths_usa_csv = csse_timeseries_url + 'time_series_covid19_deaths_US.csv'

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
        aggregate_sums_usa = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_USA_PROVINCE_STATE]).aggregate('sum')

        self.df_confirmed_by_date_usa, self.confirmed_totals_usa = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_confirmed_usa_csv,
                dropcolumns_func=drop_columns_usa,
                aggregate_func=aggregate_sums_usa,
                logtext='global time series confirmed cases',
                sum_index = 'US Total'
        )

        self.df_deaths_by_date_usa, self.deaths_totals_usa = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_deaths_usa_csv,
                dropcolumns_func=drop_columns_usa,
                aggregate_func=aggregate_sums_usa,
                logtext='global time series confirmed cases',
                sum_index = 'US Total'
            )


    def __init__(self, *args, **kwargs):
        self.__init_logger()
        self.__read_csse_daily_report()
        self.__read_csse_time_series_reports()
        pass

    def get_total_confirmed(self, scope):
        """
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: total current tally of positive cases
        """
        return self.global_totals.get(CSSE_DAILY_COL_CONFIRMED) if scope == SCOPE_WORLD else \
                self.usa_totals.get(CSSE_DAILY_COL_CONFIRMED)

    def get_total_deaths(self, scope):
        """
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: total current tally of deaths
        """
        return self.global_totals.get(CSSE_DAILY_COL_DEATHS) if scope == SCOPE_WORLD else \
                self.usa_totals.get(CSSE_DAILY_COL_DEATHS)

    def get_total_recovered(self, scope):
        """
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: total current tally of recovered cases
        """
        return self.global_totals.get(CSSE_DAILY_COL_RECOVERED) if scope == SCOPE_WORLD else \
                self.usa_totals.get(CSSE_DAILY_COL_RECOVERED)

    def get_total_active(self, scope):
        """
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: total current tally of active cases
        """
        return self.global_totals.get(CSSE_DAILY_COL_ACTIVE) if scope == SCOPE_WORLD else \
                self.usa_totals.get(CSSE_DAILY_COL_ACTIVE)


    def get_df_confirmed_by_date_world(self):
        """
        Get the dataframes for time series data on confirmed cases indexed by country
        :return: dataframes containing confirmed cases indexed by country
        """
        return self.df_confirmed_by_date_world

    def get_df_deaths_by_date_world(self):
        """
        Get the dataframes for time series data on deaths indexed by country
        :return: dataframes containing deaths indexed by country
        """
        return self.df_deaths_by_date_world

    def get_df_recovered_by_date_world(self):
        """
        Get the dataframes for time series data on recovered cases indexed by country
        :return: dataframes containing recovered indexed by country
        """
        return self.df_recovered_by_date_world

    def get_df_confirmed_by_date_usa(self):
        """
        Get the dataframes for time series data on confirmed cases indexed by state
        :return: dataframes containing confirmed cases indexed by country
        """
        return self.df_confirmed_by_date_usa

    def get_df_deaths_by_date_usa(self):
        """
        Get the dataframes for time series data on deaths indexed by state
        :return: dataframes containing deaths indexed by country
        """
        return self.df_deaths_by_date_usa

