import pandas as pd
import datetime as dt
import os
import logging
import json

# Scope
SCOPE_WORLD='Worldwide'         # worldwide scope indexed by countries
SCOPE_USA='United States'       # US scope indexed by states
SCOPE_US_COUNTIES='US Counties' # US scope indexed by counties

# Location string for overall computations
LOC_WORLD_OVERALL='Worldwide'
LOC_USA_OVERALL='US Total'

# Stats
STAT_CONFIRMED='Confirmed'
STAT_DEATHS='Deaths'
STAT_RECOVERED='Recovered'
STAT_ACTIVE='Active'

# Data frame columns

# Daily DF columns
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
CSSE_DAILY_COL_COMBINED_KEY= 'Combined_Key'
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
CSSE_TIMESERIES_COL_USA_ISO3='iso3'
CSSE_TIMESERIES_COL_USA_CODE3='code3'
CSSE_TIMESERIES_COL_USA_FIPS='FIPS'
CSSE_TIMESERIES_COL_USA_ADMIN2='Admin2'
CSSE_TIMESERIES_COL_USA_POPULATION='Population'
CSSE_TIMESERIES_COL_USA_COMBINED_KEY='Combined_Key'



def get_location(row):
    if CSSE_DAILY_COL_COMBINED_KEY in row.index:
        return row[CSSE_DAILY_COL_COMBINED_KEY]
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
add_location = lambda df: df.apply(lambda row: get_location(row), axis=1)


class CovidDataProcessor:
    __today_str = f'{dt.datetime.today():%m-%d-%Y}'
    __yesterday_str = f'{dt.datetime.today() - dt.timedelta(days=1):%m-%d-%Y}'

    __csse_base_url = './covid-19-data/csse_covid_19_data/'
    __csse_daily_url = __csse_base_url + 'csse_covid_19_daily_reports/'
    __csse_timeseries_url = __csse_base_url + 'csse_covid_19_time_series/'

    __geojson_world_countries_url = './data/countries.geo.json'
    __geojson_us_states_url = './data/us_states_500k_res.json'
    __geojson_us_counties_url = './data/us_counties_500k_res.json'

    rename_countries = {
        'Bahamas': 'The Bahamas',
        'Burma': 'Myanmar',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo',
        'Cote d\'Ivoire': 'Ivory Coast',
        'Czechia': 'Czech Republic',
        'Guinea-Bissau': 'Guinea Bissau',
        'Korea, South': 'South Korea',
        'North Macedonia': 'Macedonia',
        'Serbia': 'Republic of Serbia',
        'Eswatini': 'Swaziland',
        'Timor-Leste': 'East Timor',
        'Taiwan*': 'Taiwan',
        'Tanzania': 'United Republic of Tanzania',
        'US': 'United States of America',
        'West Bank and Gaza': 'West Bank'
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

    csse_daily_stat_to_col_map = {
        STAT_CONFIRMED: CSSE_DAILY_COL_CONFIRMED,
        STAT_DEATHS: CSSE_DAILY_COL_DEATHS,
        STAT_ACTIVE: CSSE_DAILY_COL_ACTIVE,
        STAT_RECOVERED: CSSE_DAILY_COL_RECOVERED
    }

    scope_to_totals_map = {}

    scope_and_stat_to_by_date_df_map = {
        SCOPE_WORLD: {},
        SCOPE_USA: {},
        SCOPE_US_COUNTIES: {}
    }



    def __init_logger(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        # add the handlers to logger
        self.logger.addHandler(ch)

    def __read_world_countries_geojson(self):
        with open(self.__geojson_world_countries_url) as f:
            self.geojson_world_countries = json.load(f)

    def __read_us_counties_geojson(self):
        with open(self.__geojson_us_counties_url) as f:
            self.geojson_us_counties = json.load(f)
            for feat in self.geojson_us_counties['features']:
                state_fips = feat['properties']['STATE']
                county_fips = feat['properties']['COUNTY']
                feat['id'] = state_fips + county_fips

    def __read_us_states_geojson(self):
        with open(self.__geojson_us_states_url) as f:
            self.geojson_us_states = json.load(f)

    def __check_countries_in_province_field(self, df):
        geojson = self.geojson_world_countries
        for feat in geojson['features']:
            country = feat['properties']['name']
            if not df[CSSE_DAILY_COL_COUNTRY_REGION].isin([country]).any():
                # is it in province field?
                if df[CSSE_DAILY_COL_PROVINCE_STATE].isin([country]).any():
                    matching_rows = df[df[CSSE_DAILY_COL_PROVINCE_STATE] == country]
                    if not matching_rows.empty:
                        self.logger.warning(f'{country} found in state/province field of datastet, copying to country field')
                        matching_rows[CSSE_DAILY_COL_COUNTRY_REGION].iloc[0] = country
                    continue
                if self.logger is not None:
                    self.logger.warning(f'{country} not found in dataset')
                continue

    def __read_csse_daily_report(self):
        csse_daily_csv = self.__csse_daily_url + self.__today_str + '.csv'
        if not os.path.isfile(csse_daily_csv):
            csse_daily_csv = self.__csse_daily_url + self.__yesterday_str + '.csv'
        self.logger.info('Reading f{csse_daily_csv}...')
        df_daily_global = pd.read_csv(csse_daily_csv, dtype={CSSE_DAILY_COL_FIPS: str})

        self.__check_countries_in_province_field(df_daily_global)

        # make a world countries data frame
        self.logger.info('processing daily global data...')
        self.df_daily_world = df_daily_global.drop(
            columns=[CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_PROVINCE_STATE, CSSE_DAILY_COL_ADMIN2, CSSE_DAILY_COL_COMBINED_KEY])
        self.df_daily_world = self.df_daily_world.groupby(
            self.df_daily_world[CSSE_DAILY_COL_COUNTRY_REGION]).aggregate(self.daily_aggregation_functions)
        self.df_daily_world.rename(self.rename_countries, inplace=True)
        self.df_daily_world.sort_index(inplace=True)
        self.df_daily_world[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_world)

        # compute global totals
        self.logger.info('computing global daily totals...')
        self.global_totals = self.df_daily_world.aggregate(self.daily_aggregation_functions)
        self.scope_to_totals_map[SCOPE_WORLD] = self.global_totals

        # make a US counties dataframe
        self.logger.info('Deriving data for US counties...')
        self.df_daily_us_counties = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        # drop rows with NaN in FIPS column
        self.df_daily_us_counties = self.df_daily_us_counties[self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].notna()]
        self.df_daily_us_counties[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_us_counties)
        self.df_daily_us_counties[CSSE_DAILY_COL_FIPS] = self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].astype(str)
        self.df_daily_us_counties[CSSE_DAILY_COL_FIPS] = self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].apply('{:0>5}'.format)
        self.df_daily_us_counties.set_index(keys=CSSE_DAILY_COL_FIPS, inplace=True)

        # make a US states dataframe
        self.logger.info('Deriving data for US states...')
        self.df_daily_us_states = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        self.df_daily_us_states.drop(columns=[CSSE_DAILY_COL_FIPS])
        self.df_daily_us_states = \
            self.df_daily_us_states.groupby(self.df_daily_us_states[CSSE_DAILY_COL_PROVINCE_STATE]).aggregate('sum')
        self.df_daily_us_states[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_us_states)

        # compute us totals
        self.logger.info('computing US daily totals...')
        self.usa_totals = self.df_daily_us_counties.aggregate(self.daily_aggregation_functions)
        self.scope_to_totals_map[SCOPE_USA] = self.usa_totals
        self.scope_to_totals_map[SCOPE_US_COUNTIES] = self.usa_totals

    def __get_csse_time_series_data(self, url, set_index=None, sum_index='Total', dropcolumns_func=None, aggregate_func=None, logtext=None, rename_countries=False):
        if logtext is not None:
            self.logger.info(f'Reading {logtext} data from {url}...')
        df = pd.read_csv(url)

        if set_index is not None:
            df.set_index(keys=set_index, inplace=True)
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
        df = pd.concat([df_sum, df], sort=False)
        df1_transposed = df.transpose()
        df1_transposed.index = pd.to_datetime(df1_transposed.index)
        return df1_transposed, sum

    def __read_csse_time_series_reports(self):
        drop_columns_global = lambda df: df.drop(
            columns=[
                CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE,
                CSSE_TIMESERIES_COL_GLOBAL_LATITUDE,
                CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE],
            inplace=True
        )

        aggregate_sums_global = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION]).aggregate('sum')

        csse_timeseries_confirmed_global_csv = self.__csse_timeseries_url + 'time_series_covid19_confirmed_global.csv'
        csse_timeseries_deaths_global_csv = self.__csse_timeseries_url + 'time_series_covid19_deaths_global.csv'
        csse_timeseries_recovered_global_csv = self.__csse_timeseries_url + 'time_series_covid19_recovered_global.csv'

        self.df_confirmed_by_date_world, self.confirmed_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_confirmed_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series confirmed cases',
                rename_countries=True,
                sum_index=LOC_WORLD_OVERALL
            )

        self.scope_and_stat_to_by_date_df_map[SCOPE_WORLD][STAT_CONFIRMED] = self.df_confirmed_by_date_world

        self.df_deaths_by_date_world, self.deaths_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_deaths_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series deaths',
                rename_countries=True,
                sum_index = LOC_WORLD_OVERALL
        )

        self.scope_and_stat_to_by_date_df_map[SCOPE_WORLD][STAT_DEATHS] = self.df_deaths_by_date_world

        self.df_recovered_by_date_world, self.recovered_totals_global = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_recovered_global_csv,
                dropcolumns_func=drop_columns_global,
                aggregate_func=aggregate_sums_global,
                logtext='global time series recovered cases',
                rename_countries=True,
                sum_index = LOC_WORLD_OVERALL
        )

        self.scope_and_stat_to_by_date_df_map[SCOPE_WORLD][STAT_RECOVERED] = self.df_recovered_by_date_world


        csse_timeseries_confirmed_usa_csv = self.__csse_timeseries_url + 'time_series_covid19_confirmed_US.csv'
        csse_timeseries_deaths_usa_csv = self.__csse_timeseries_url + 'time_series_covid19_deaths_US.csv'

        drop_columns_usa = lambda df: df.drop(
            columns=[
                CSSE_TIMESERIES_COL_USA_COUNTRY_REGION,
                CSSE_TIMESERIES_COL_USA_LATITUDE,
                CSSE_TIMESERIES_COL_USA_LONGITUDE,
                CSSE_TIMESERIES_COL_USA_UID,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_ISO3,
                CSSE_TIMESERIES_COL_USA_CODE3,
                CSSE_TIMESERIES_COL_USA_FIPS,
                CSSE_TIMESERIES_COL_USA_POPULATION
            ],
            inplace=True,
            errors='ignore'
        )
        aggregate_sums_usa = lambda df: df.groupby(df[CSSE_TIMESERIES_COL_USA_PROVINCE_STATE]).aggregate('sum')

        self.df_confirmed_by_date_usa, self.confirmed_totals_usa = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_confirmed_usa_csv,
                dropcolumns_func=drop_columns_usa,
                aggregate_func=aggregate_sums_usa,
                logtext='USA time series confirmed cases',
                sum_index = LOC_USA_OVERALL
        )

        self.scope_and_stat_to_by_date_df_map[SCOPE_USA][STAT_CONFIRMED] = self.df_confirmed_by_date_usa

        self.df_deaths_by_date_usa, self.deaths_totals_usa = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_deaths_usa_csv,
                dropcolumns_func=drop_columns_usa,
                aggregate_func=aggregate_sums_usa,
                logtext='USA time series deaths',
                sum_index = LOC_USA_OVERALL
            )

        self.scope_and_stat_to_by_date_df_map[SCOPE_USA][STAT_DEATHS] = self.df_deaths_by_date_usa

        drop_columns_us_counties = lambda df: df.drop(
            columns=[
                CSSE_TIMESERIES_COL_USA_COUNTRY_REGION,
                CSSE_TIMESERIES_COL_USA_PROVINCE_STATE,
                CSSE_TIMESERIES_COL_USA_LATITUDE,
                CSSE_TIMESERIES_COL_USA_LONGITUDE,
                CSSE_TIMESERIES_COL_USA_UID,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_ISO3,
                CSSE_TIMESERIES_COL_USA_ADMIN2,
                CSSE_TIMESERIES_COL_USA_CODE3,
                CSSE_TIMESERIES_COL_USA_FIPS,
                CSSE_TIMESERIES_COL_USA_POPULATION
            ],
            inplace=True,
            errors='ignore'
        )


        self.df_confirmed_by_date_us_counties, self.confirmed_totals_us_counties = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_confirmed_usa_csv,
                dropcolumns_func=drop_columns_us_counties,
                logtext='US counties time series confirmed cases',
                sum_index = LOC_USA_OVERALL,
                set_index = CSSE_TIMESERIES_COL_USA_COMBINED_KEY
        )

        self.scope_and_stat_to_by_date_df_map[SCOPE_US_COUNTIES][STAT_CONFIRMED] = self.df_confirmed_by_date_us_counties

        self.df_deaths_by_date_us_counties, self.deaths_totals_us_counties = \
            self.__get_csse_time_series_data(
                url=csse_timeseries_deaths_usa_csv,
                dropcolumns_func=drop_columns_us_counties,
                logtext='US counties time series deaths',
                sum_index = LOC_USA_OVERALL,
                set_index=CSSE_TIMESERIES_COL_USA_COMBINED_KEY
        )

        self.scope_and_stat_to_by_date_df_map[SCOPE_US_COUNTIES][STAT_DEATHS] = self.df_deaths_by_date_us_counties
        pass

    def __init__(self, *args, **kwargs):
        self.__init_logger()
        self.__read_world_countries_geojson()
        self.__read_us_states_geojson()
        self.__read_us_counties_geojson()
        self.__read_csse_daily_report()
        self.__read_csse_time_series_reports()
        pass

    def get_geojson(self, scope):
        """
        :return: parsed geoJSON based on scope
        """
        if scope == SCOPE_WORLD:
            return self.geojson_world_countries
        elif scope == SCOPE_USA:
            return self.geojson_us_states
        elif scope == SCOPE_US_COUNTIES:
            return self.geojson_us_counties
        else:
            return None

    def get_stat_by_date_df(self, scope, stat):
        """
        return dataframe containing stat by date
        :param scope: SCOPE_WORLD or other defined scope
        :param stat: stat to return in dataframe (STAT_CONFIRMED, STAT_DEATHS etc)
        :return: dataframe containing requested stats per location (defined by scope) by date
        """
        if scope not in self.scope_and_stat_to_by_date_df_map:
            self.logger.error(f'No data available for scope={scope}')
            return None
        stat_map = self.scope_and_stat_to_by_date_df_map[scope]
        if stat not in stat_map:
            self.logger.error(f'No data found for stat={stat} under scope={scope}')
            return None
        df = stat_map[stat]
        return df

    def get_latest_stat(self, stat, scope, loc=None):
        """

        :param scope:
        :param location:
        :return:
        """
        df = self.get_stat_by_date_df(scope, stat)
        df_diff = df.diff()
        df_pct_change = df.pct_change()
        latest_date = df.index.max()
        if loc is None:
            loc = get_location_overall(scope)
        value = df.loc[latest_date, loc]
        pct_change = df_pct_change.loc[latest_date, loc] * 100
        diff = df_diff.loc[latest_date, loc]
        return value, diff, pct_change


    def get_df_daily_report(self, scope):
        """
        Get the data frame for the Covid-19 daily report indexed by locations depending on scope
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: data frame containing daily reports of confirmed cases deaths and recovered cases
        which are obtained from the columns CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_DEATHS,
        CSSE_DAILY_COL_RECOVERED and CSSE_DAILY_COL_ACTIVE. Also CSSE_DAILY_COL_LATITUDE and
        CSSE_DAILY_COL_LONGITUDE provides the central lat and long coordinates for the location
        TODO: add specifics for world and US county data frames
        """
        if scope == SCOPE_WORLD:
            return self.df_daily_world
        elif scope == SCOPE_USA:
            return self.df_daily_us_states
        elif scope == SCOPE_US_COUNTIES:
            return self.df_daily_us_counties
        else:
            return None

    def get_top_locations(self, scope, stat, n=10):
        df = self.get_df_daily_report(scope).nlargest(n=n, columns=[stat])
        df.set_index(add_location(df), inplace=True)
        return df

    def get_bottom_locations(self, scope, stat, n=10):
        df = self.get_df_daily_report(scope)
        df1 = df.dropna()
        df1 = df1.nsmallest(n=n, columns=[stat])

        df1.set_index(add_location(df1), inplace=True)
        return df1


def get_scopes():
    return [SCOPE_WORLD, SCOPE_USA, SCOPE_US_COUNTIES]

def get_location_overall(scope):
    if scope == SCOPE_WORLD:
        return LOC_WORLD_OVERALL
    elif scope == SCOPE_USA:
        return LOC_USA_OVERALL
    elif scope == SCOPE_US_COUNTIES:
        return LOC_USA_OVERALL
    return 'Not implemented'