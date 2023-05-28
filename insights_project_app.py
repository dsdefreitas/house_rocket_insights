import folium
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from folium.plugins  import MarkerCluster
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

st.set_page_config(layout = 'wide')

with st.sidebar:
    selected = option_menu('Menu', ['Introduction', 'Insights', 'Results'], icons=['house', 'lightbulb', 'bookmark-check'], menu_icon='cast', default_index=0)

@st.cache(allow_output_mutation= True)

def get_data(path1, path2):
    data = pd.read_csv(path1)
    data_address = pd.read_csv(path2)
    data = pd.merge(data, data_address, on='id', how='inner').drop(columns=['query'],axis=1)
    return data

def data_manipulation(data):

    #apagando id's duplicados 
    data.drop_duplicates(subset=['id'], inplace=True, keep='first') 

    #convertendo a coluna date para o tipo datetime
    data['date'] = pd.to_datetime(data['date'])

    #definindo uma data e hora padrão para células contendo zero.
    data['yr_renovated'] = data['yr_renovated'].apply(lambda x: pd.to_datetime(1900, format='%Y') if x == 0 else pd.to_datetime(x, format='%Y'))

    #especificando quais propriedades foram reformadas.
    data['renovated'] = data.apply(lambda line: 'no' if line['yr_renovated'] == pd.to_datetime(1900, format='%Y') else 'yes', axis=1)

    #convertendo a coluna yr_built em datetime.
    data['yr_built'] = pd.to_datetime(data['yr_built'], format='%Y')

    #Excluindo a linha do imóvel contendo 33 quartos, considerado um erro de digitação.
    data = data.drop(data[data['bedrooms'] == 33].index)

    #definindo quais propriedades têm um porão e quais não.
    data['basement'] = data['sqft_basement'].apply(lambda line: 'without basement' if line == 0 else 'with basement')

    #criando uma coluna com ano.
    data['year'] = data['date'].dt.year

    #criando uma coluna com a estação do ano.
    data['season'] = data['date'].apply(data_season)

    #detalhando quais casas têm vista para o mar e quais não.
    data['waterfront'] = data['waterfront'].apply(lambda line: 'yes' if line == 1 else 'no')

    #detalhando quais casas têm vista para o mar e quais não.
    data['bathrooms'] = data['bathrooms'].apply(lambda line: round(line, 2))

    return data

def data_season(line):
    
    if line.month == 6 or line.month == 7 or line.month == 8:
        return 'summer'
    elif line.month == 9 or line.month == 10 or line.month == 11:
        return 'autumn'
    elif line.month == 12 or line.month == 1 or line.month == 2:
        return 'winter'
    else:
        return 'spring'

def suggested_map(data):

    density_map = folium.Map(location=[data['lat'].mean(), data['long'].mean()],
                             default_zoom_start=15)

    marker_cluster = MarkerCluster().add_to(density_map)

    for name, row in data.iterrows():

        folium.Marker([row['lat'],  row['long'] ], popup = 'id: {0}. price: U${1}'.format(row['id'], row['price'])).add_to(marker_cluster)

    folium_static(density_map)

    return None

def view_financial_results_and_map(purchase_table): 
        
    number = len(purchase_table.index)
    sp_sum = purchase_table['price'].sum()
    profit_sum = purchase_table['profit'].sum()

    results_table = {'Number of Properties': number, 'Total Investiment (U$)': sp_sum, 'Total Profit (U$)': profit_sum}

    results_table = pd.DataFrame(results_table, index=[''])

    st.dataframe(purchase_table)
    st.title('Financial Result Table')
    st.dataframe(results_table)

    st.title('Map of suggested properties')

    grouped_map = purchase_table[['id', 'price', 'lat', 'long']]

    suggested_map(grouped_map)

    return None 

def introduction():

    if selected == 'Introduction':

        st.title('The House Hocket Project')
        st.write('')
        st.write('The House Rocket is a digital platform whose business model is the purchase and sale of real estate using technology.')
        st.write('Their main strategy is to buy houses in good condition, with great locations, at low prices and then resell them at higher prices, thus increasing the company\'s profit and revenue.')
        st.write('However, the business team has to deal with several variables that influence the price, making them more or less attractive to buyers and sellers; Also the amount of data is large, and it would take a lot of time to do the work manually.')
        st.write('The purpose of this application is to help the CEO to decide which are the best homes to buy and what are the best prices and time of year to sell them; as well as display the profit made.')

        st.title('Assumptions')

        st.write(':black_medium_small_square: The line corresponding to a property with 33 bedrooms has been removed as it was considered a typo. ')
        st.write(':black_medium_small_square: Properties with a renewal year equal to zero or yr_renovated column = 0 were considered without renovation. ')
        st.write(':black_medium_small_square: Properties with basement area equal to zero or sqft_basement column = 0 were considered as without basement. ')
        st.write(':black_medium_small_square: This is an initial project that will be improved as the author\'s skills evolve.')

        st.title('The Product')

        st.write('A table of suggestions that selects properties in excellent condition and prices lower than the average prices of their respective regions. 10 business hypotheses were evaluated to generate insights, presented in the "insights" tab. You can narrow down table suggestions from filters based on these insights. Furthermore, a competitive sale price for the market is suggested and capable of generating a considerable profit, in addition to the best season of the year to sell the property purchased. A map is also displayed to identify the location of properties suggested by the id, which changes along with the filters.')
        st.write('')
        st.write('It is also presented the profit and the total investment of the suggestions that varies according to the chosen filters. The maximum number of properties to be recommended is 3775, the maximum investment is U\$1,483,480,263 and the maximum profit earned is U\$315,284,211.')

def insights(data):

    if selected == 'Insights':

        st.title('Hypothesis')

        col1, col2 = st.columns(2)

        with col1:

            #Hipótese 1  
            st.subheader('H1')
            st.write('Properties that overlook the water are 30% more expensive, on average.')
            st.caption(f'That\'s Incorrect. Waterfront properties are 212.60% more expensive.')

            water_front_median = data[['price', 'waterfront']].groupby('waterfront').mean().reset_index()

            graph = px.bar(water_front_median, x='waterfront', y='price', labels={
                "waterfront": "Waterfront?", "price": "Average Price (U$)"
            }
                            )


            st.plotly_chart(graph, use_container_width=True)

            # Hipótese 2 
            st.subheader('H2')
            st.write('Properties with a construction date less than 1955 are 50% cheaper, on average.')
            st.caption(f'That\'s Incorrect. Properties with a construction date less than 1955 are 1.09% cheaper, on average.')

            dt_before_1955 = data[data['yr_built'] < pd.to_datetime(1955, format='%Y')]['price'].mean()
            dt_after_1955 = data[data['yr_built'] > pd.to_datetime(1955, format='%Y')]['price'].mean()

            column_0 = ['before 1955', 'after 1955']
            column_1 = [dt_before_1955, dt_after_1955]

            h2 = {
                'Construction Period': column_0,
                'Price': column_1
            }

            yr_built_1955 = pd.DataFrame(h2, index=[0, 1])

            graph = px.bar(yr_built_1955, x='Construction Period', y='Price')

            st.plotly_chart(graph, use_container_width=True)

            #Hipótese 3 
            st.subheader('H3')
            st.write('Properties without a basement are 50% larger than those with a basement.')
            st.caption('That\'s Incorrect. Properties without a basement are 19.82% smaller than those with a basement.')

            basement = data[['basement', 'sqft_living']].groupby('basement').mean().reset_index()

            graph = px.bar(basement, x='basement', y='sqft_living', labels={
                "basement": "Structure", "sqft_living": "Average Area (m²)"
            }
                            )

            st.plotly_chart(graph, use_container_width=True)

            variation = round(
                ((basement.loc[1, 'sqft_living'] / basement.loc[0, 'sqft_living']) - 1) * 100, 2)

            # Hipótese 4 
            st.subheader('H4')
            st.write('YoY (Year over Year) property price growth is 10%')
            st.caption('That\'s Incorrect. YoY property price growth is 0.72%')

            price_date = data[['price', 'year']].groupby('year').mean().reset_index()

            graph = px.bar(price_date, x='year', y='price', labels={
                "year": "Year", "price": "Average Price (U$)"
            }
                            )

            graph.update_xaxes(type='category',
                                tickvals=[2014, 2015],
                                ticktext=['2014', '2015']
                                )

            st.plotly_chart(graph, use_container_width=True)

            # Hipótese 5

            st.subheader('H4')
            st.write('Homes with 3 bathrooms have a MoM (Month over Month) growth of 15%')
            st.caption('That\'s Incorrect. YoY property price growth has no pattern')

            mom_3_bathrooms = data.loc[data['bathrooms'] == 3, ['price', 'date']]

            mom_3_bathrooms['date'] = pd.to_datetime(mom_3_bathrooms['date'].dt.strftime('%m-%Y'))

            mom_3_bathrooms = mom_3_bathrooms.groupby('date').mean().reset_index()

            mom_3_bathrooms['percentage change'] = mom_3_bathrooms['price'].pct_change() * 100

            mom_3_bathrooms['variation sign'] =  mom_3_bathrooms['percentage change'].apply(lambda x: 'positive' if x > 0 else 'negative')

            graph4_1 = px.line(mom_3_bathrooms, x='date', y='price', labels={
                "date": "Month/Year", "price": "Average Price (U$)"
            }
                            )

            graph4_2 = px.bar(data_frame=mom_3_bathrooms, x='date', y='percentage change', color="variation sign", barmode="group",
                   labels={"percentage change": "Average Price Variation (%)", "date": " "},
                   color_discrete_map={
                       'negative': '#EF553B',
                       'positive': '#636EFA'
                   }
                   )

            st.plotly_chart(graph4_1, use_container_width=True)
            st.plotly_chart(graph4_2, use_container_width=True)

        with col2:

            #Hipótese 6:

            st.subheader('H6')
            st.write('Properties renovated from the year 2000 onwards are, on average, 25% more expensive.')
            st.caption('That\'s Incorrect.  Properties renovated after 2000 are on average 43.22% more expensive.')

            yr_renovated_price = data[['yr_renovated', 'price']].groupby('yr_renovated').mean().reset_index()
            yr_renovated_price = yr_renovated_price.drop(yr_renovated_price[yr_renovated_price['yr_renovated'] == pd.to_datetime(1900, format='%Y')].index)

            price_before_2000 = yr_renovated_price[yr_renovated_price['yr_renovated'] < pd.to_datetime(2000, format='%Y')]
            price_after_2000 = yr_renovated_price[yr_renovated_price['yr_renovated'] >= pd.to_datetime(2000, format='%Y')]

            coluna_1 = ['Before 2000', 'After 2000']
            coluna_2 = [price_before_2000['price'].mean(), price_after_2000['price'].mean()]

            yr_renovated_price = {'Reform Period': coluna_1, 'Average Price (U$)': coluna_2}

            yr_renovated_price = pd.DataFrame(yr_renovated_price)

            graph = px.bar(yr_renovated_price, x='Reform Period', y='Average Price (U$)')
            st.plotly_chart(graph, use_container_width=True)

            # Hipótese 7:

            st.subheader('H7')
            st.write('Properties with up to 2 bedrooms are, on average, 20% cheaper.')
            st.caption('That\'s Incorrect.  Properties with up to 2 bedrooms are, on average, 37% cheaper.')

            bedroom_smallest_2 = data[data['bedrooms'] <= 2]['price'].mean()
            bedroom_larger_2 = data[data['bedrooms'] >= 2]['price'].mean()

            column_0 = ['Up to 2', 'More than 2']
            column_1 = [bedroom_smallest_2, bedroom_larger_2]

            number_bedrooms_price = {'Number of bedrooms': column_0, 'Average Price (U$)': column_1}
            number_bedrooms_price = pd.DataFrame(number_bedrooms_price)

            graph = px.bar(number_bedrooms_price, x='Number of bedrooms', y='Average Price (U$)')
            st.plotly_chart(graph, use_container_width=True)

            # Hipótese 8:

            st.subheader('H8')
            st.write('Renovated properties are 40% more expensive than unrenovated properties.')
            st.caption('That\'s Correct! Renovated properties are 43.37% more expensive than unrenovated properties.')

            unrenovated_price = data[data['yr_renovated'] == pd.to_datetime('1900', format='%Y')]['price'].mean()
            renovated_price = data[data['yr_renovated'] != pd.to_datetime('1900', format='%Y')]['price'].mean()

            column_0 = ['unrenovated', 'renovated']
            column_1 = [unrenovated_price, renovated_price]

            reform = {'Condition': column_0, 'Average Price (U$)': column_1}
            reform = pd.DataFrame(reform)

            graph = px.bar(reform, x='Condition', y='Average Price (U$)')
            st.plotly_chart(graph, use_container_width=True)

            # Hipótese 9 :

            st.subheader('H9')
            st.write('The best time to buy real estate is in winter, which is 20% cheaper than the rest of the year.')
            st.caption('It is true that winter is the best time to buy real estate, however real estate is 4.85% cheaper in this period.')

            #Qual estação do ano é a melhor?

            season_price = data[['season', 'price']].groupby('season').mean().reset_index()

            graph9_1 = px.bar(season_price, x='season', y='price', labels={
                "season": "Real State Buying Season", "price": "Average Price (U$)"
            }
                            )

            #Em qual porcentagem?
            price_winter = data[data['season'] == 'winter']['price'].mean()
            price_rest_of_the_year = data[data['season'] != 'winter']['price'].mean()

            coluna_0 = ['winter', 'rest of the year']
            coluna_1 = [price_winter, price_rest_of_the_year]

            winter = {'Property buying season': coluna_0, 'Average Price (U$)': coluna_1}
            winter = pd.DataFrame(winter)

            graph9_2 = px.bar(winter, x='Property buying season', y='Average Price (U$)')

            st.plotly_chart(graph9_1, use_container_width=True)
            st.plotly_chart(graph9_2, use_container_width=True)

            # Hipótese 10:

            st.subheader('H10')
            st.write('Properties with better conditions are on average 20% more expensive')
            st.caption('That\'s Incorrect! Properties with best conditions are on average 0.46% more expensive.')

            best_conditions = data[(data['condition'] == 4) | (data['condition'] == 5)]['price'].mean()
            worst_conditions = data[(data['condition'] != 4) & (data['condition'] != 5)]['price'].mean()

            variation = abs(round(((best_conditions /worst_conditions) - 1) * 100, 2))

            column_0 = ['best', 'worst']
            column_1 = [best_conditions, worst_conditions]

            conditions = {'Property condition': column_0, 'Average Price (U$)': column_1}
            conditions = pd.DataFrame(conditions)

            graph = px.bar(conditions, x='Property condition', y='Average Price (U$)')
            st.plotly_chart(graph, use_container_width=True)

        st.title('Main Insights')
        st.write('')
        st.write(':black_medium_small_square: Given that beachfront properties are 212.64% more expensive, it is recommended not to buy them ')
        st.write(':black_medium_small_square: Since renovated properties are 43.37% of those not renovated and the renovation period still increases the price (renovated after 2000 are on average 43.48% more expensive), it is recommended to buy unrenovated properties and renovate them afterwards.')
        st.write(':black_medium_small_square: Since properties with up to 2 bedrooms are, on average, 37% cheaper, it is recommended to choose them.')
        st.write(':black_medium_small_square: As properties purchased in winter are, on average, 4.85% cheaper than the rest of the year, it is suggested to purchase more properties in this period. ')
        st.write(':black_medium_small_square: Since properties with better conditions are on average 0.6% more expensive, and since conditions do not influence the purchase price much, always opt for properties with best conditions.')

def results(data):

    if selected == 'Results':

        #Tabela de Sugestão
        st.title('Suggested Properties Table')

        #criando tabela com a coluna de média de preço por região
        data_grouped = data[['zipcode', 'price']].groupby('zipcode').median().reset_index()
        data_grouped = data_grouped.rename(columns={'price': 'region_median_price'})
        data_with_region_median = pd.merge(data, data_grouped, on='zipcode', how='inner')

        #selecionando as colunas que vão para a tabela de sugestão
        purchase_table = data_with_region_median[['id', 'zipcode', 'road', 'house_number', 'price', 'region_median_price', 'yr_built', 'waterfront', 'renovated', 'bedrooms', 'bathrooms',
        'season', 'condition', 'lat', 'long']]

        #criando coluna de status de sugestão
        purchase_table['status'] = purchase_table.apply(lambda line: 'suggested' if (line['condition'] >= 4) and (line['price'] < line['region_median_price']) else 'not suggested', axis=1)

        #melhorando leitura do título das colunas
        purchase_table.rename(columns = {'season': 'season_of_sale', 'yr_built': 'construction_year'}, inplace = True)

        #filtrando apenas os imóveis sugeridos
        purchase_table = purchase_table[purchase_table['status'] == 'suggested']

        #criando coluna de melhor preço por estação
        p_z_c_s = purchase_table[['zipcode', 'season_of_sale', 'price']].groupby(['zipcode', 'season_of_sale']).median().reset_index().sort_values(['zipcode', 'price'])
        p_z_c_s = p_z_c_s.drop_duplicates(subset='zipcode', keep='last')
        p_z_c_s = p_z_c_s.rename(columns={'season_of_sale': 'best_season_to_sell', 'price': 'best_price_per_season'})
        purchase_table = pd.merge(purchase_table, p_z_c_s, on='zipcode', how='inner')

        #criando coluna de preço sugerido
        purchase_table['suggested_price'] = purchase_table.apply( lambda line: (line['price'] + (line['price'] * 0.30)) if line['price'] < line[
        'best_price_per_season'] else (line['price'] + line['price'] * 0.10), axis=1)

        #criando coluna de lucro
        purchase_table['profit'] = purchase_table.apply(lambda line: line['suggested_price'] - line['price'], axis=1)

        #transformando o tipo da coluna construction_year para datetime
        purchase_table['construction_year'] = purchase_table['construction_year'].dt.strftime('%Y')

        #apagando colunas auxiliares 
        purchase_table.drop(columns = ['region_median_price', 'season_of_sale', 'best_price_per_season', 'status'], inplace = True)

        #tirando virgulas separando dezenas da visualização do streamlit para colunas id e zipcode. 
        purchase_table['id'] = purchase_table['id'].astype(str)
        purchase_table['zipcode'] = purchase_table['zipcode'].astype(str)
 
        st.title('Insights Filter')
        col1, col2, col3 = st.columns(3)
        with col1:
            insight1 = st.checkbox('Remove renovated properties?', value=False)
        with col2:
            insight2 = st.checkbox('Remove properties with a water view?', value=False)
        with col3:
            insight3 = st.slider('Up to how many rooms?', 1, 11, 11)

        if insight1 == False and insight2 == False:

            purchase_table1 = purchase_table[purchase_table['bedrooms'] <= insight3]

            view_financial_results_and_map(purchase_table1)

        elif insight1 == True and insight2 == False:

            purchase_table2 = purchase_table[(purchase_table['bedrooms'] <= insight3) & (purchase_table['renovated'] == 'no')]

            view_financial_results_and_map(purchase_table2)

        elif insight1 == False and insight2 == True:
            purchase_table3 = purchase_table[(purchase_table['bedrooms'] <= insight3) & (purchase_table['waterfront'] == 'no')]

            view_financial_results_and_map(purchase_table3)

        elif insight1 == True and insight2 == True:
            purchase_table4 = purchase_table[(purchase_table['bedrooms'] <= insight3) & (purchase_table['waterfront'] == 'no') & (purchase_table['renovated'] == 'no')]

            view_financial_results_and_map(purchase_table4)


if __name__ == '__main__':
    path1 = r"data/kc_house_data.csv"
    path2 = r"data/address.csv"
    data = get_data(path1, path2)
    data = data_manipulation(data)
    introduction()
    insights(data)
    results(data)



