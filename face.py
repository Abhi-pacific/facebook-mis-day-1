import pandas as pd
import streamlit as st

class Data_file:
    def __init__(self,data,beginning_date,ending_date):
        self.data = data
        self.beginning_date,self.ending_date = beginning_date,ending_date
        data = pd.ExcelFile(self.data,engine='openpyxl')
        self.raw_data = data.parse('Main File')
        self.data_manipulation()
    
    def data_manipulation(self):
        self.closure_day = self.raw_data['Case Creation time'].dt.day
        self.closure_hour = self.raw_data['Case Creation time'].dt.hour
        # Condition for beginning_date: Evening (7 PM to 11 PM)
        self.cond_beginning = (self.closure_day == self.beginning_date) & self.closure_hour.between(19, 23, inclusive='both')

        # Condition for ending_date: Midnight to 6 PM
        self.cond_ending = (self.closure_day == self.ending_date) & self.closure_hour.between(0, 18, inclusive='both')
        self.raw_data_07_to_07 = self.raw_data[self.cond_beginning | self.cond_ending]

        self.raw_data_07_to_07.reset_index(drop=True,inplace=True)
        self.raw_data_07_to_07['Sentiment Changed To'].fillna("N/A", inplace=True)
        self.unique_data = self.raw_data_07_to_07.drop_duplicates(subset=['Case Reference Id'])
        self.unique_data.reset_index(drop=True,inplace=True)

        # Calculating the FRT 
        self.closure_day_frt = self.raw_data_07_to_07['Case Creation time'].dt.day
        self.closure_hour_frt = self.raw_data_07_to_07['Case Creation time'].dt.hour

        self.frt_data = self.raw_data_07_to_07
        self.frt_date = self.frt_data['Case Creation time'].dt.day

        # Condition for date
        self.frt_data_date_condition = (self.closure_day_frt == self.ending_date) & self.closure_hour_frt.between(9, 17, inclusive='both')

        # Creating the FRT data with condition.

        self.frt_data = self.frt_data[self.frt_data_date_condition]
        self.temp = self.frt_data['Case Status'].isin(['Awaiting Customer Response','Closed'])
        self.frt_data = self.frt_data[self.temp]

        self.frt_data.dropna(subset=['Case Creation time','Case First Response Time'],inplace=True)
        self.frt_data.drop_duplicates(subset=['Case First Response Time'],inplace=True)
        self.frt_data.reset_index(drop=True,inplace=True)
        self.frt_data['FRT'] = self.frt_data['Case First Response Time'] - self.frt_data['Case Creation time']
        self.frt_data['Latency'] = self.frt_data['Case First advisor assign time'] - self.frt_data['Case Creation time']
        self.frt_data['bin Latency'] = self.frt_data['Case Last bin Received time'] - self.frt_data['Case Creation time']

        # frt 10 min condition
        self.condition_for_frt_1 = (self.frt_data['FRT'].dt.components['minutes'] > 10) & (self.frt_data['Latency'].dt.components['minutes'] > 1)
        self.frt_data = self.frt_data[~(self.condition_for_frt_1)]
        self.frt_data['Latency'] = self.frt_data['Latency'].astype(str).str.split('days').str[1]
        self.frt_data['bin Latency'] = self.frt_data['bin Latency'].astype(str).str.split('days').str[1]

        # calculating the pivot for number of brand messages
        self.pivot_unique_data = self.unique_data[self.unique_data['Case Status'].isin(['Closed','Awaiting Customer Response','Assigned'])]
        self.pivot_unique_data = self.pivot_unique_data[self.pivot_unique_data['Case Creation time'].dt.day == self.ending_date]
        self.pivot_unique_data = self.pivot_unique_data[self.pivot_unique_data['Case Creation time'].dt.hour.between(9,17,inclusive='both')]
        self.pivot_unique_data.reset_index(drop=True,inplace=True)

        # pivot code for brand messages
        self.sum_of_brandMessage = self.pivot_unique_data.pivot_table(index='Case First Assigned to Advisor',columns='Case Status',values='Number of Brand Messages',aggfunc='sum',margins=True,margins_name='Grand Total',fill_value=0)

        # Created the Sentiment Table(Pivot)
        self.sentiment_change = self.raw_data_07_to_07.pivot_table(index='Sentiment Changed To', aggfunc='size').reset_index(name='count')

        # Total number of Brand Messages
        self.brand_message = pd.DataFrame({'Sum of number of brands': [self.raw_data_07_to_07['Number of Brand Messages'].sum()]})

        # Count of Case Type
        self.count_case_type = self.raw_data_07_to_07.pivot_table(index='Case Type', aggfunc='size').reset_index(name='Count')

        self.count_case_type_T = pd.DataFrame(self.count_case_type.sum(axis=0)).T
        self.count_case_type_T['Case Type'] = 'Grand Total'
        self.count_case_type = pd.concat([self.count_case_type,self.count_case_type_T])


        # LOB
        self.count_final_lob = self.raw_data_07_to_07.pivot_table(index='Final Lob',aggfunc='size').reset_index(name = 'Count')

        # count_final_lob
        self.count_final_lob_T = pd.DataFrame(self.count_final_lob.sum(axis=0)).T
        self.count_final_lob_T['Final Lob'] = 'Grand Total'
        self.count_final_lob = pd.concat([self.count_final_lob,self.count_final_lob_T])
        self.visulazation(self.frt_data,self.sum_of_brandMessage,self.sentiment_change,self.brand_message,self.count_case_type,self.count_final_lob)

    def visulazation(self,frt_data,sum_of_brandMessage,sentiment_change,brand_message,count_case_type,count_final_lob):
        self.frt_data,self.sum_of_brandMessage,self.sentiment_change,self.brand_message,self.count_case_type,self.count_final_lob = frt_data,sum_of_brandMessage,sentiment_change,brand_message,count_case_type,count_final_lob

        st.write('FRT ')
        st.dataframe(self.frt_data)
        st.write('Sum of Brand messages')
        st.dataframe(self.sum_of_brandMessage)
        st.write('Sentiment Change')
        st.dataframe(self.sentiment_change)
        st.write('Brand Message')
        st.dataframe(self.brand_message)
        st.write('Count of case type')
        st.dataframe(self.count_case_type)
        st.write('Count of final Lob')
        st.dataframe(self.count_final_lob)








col1, col2, col3 = st.columns([0.1,4,1])
with col3:
    st.image('https://www.netimpactlimited.com/wp-content/uploads/2024/04/NetImpact-Logo-Final-Web-2.png')
with col2:
    st.title('Facebook 📊')
data = st.file_uploader(f'Please Upload the Excel file for the Facebook data')
beginning_date = st.number_input('Please Enter the Begginning date',min_value=1,max_value=31,step=1)
ending_date = st.number_input('Enter the ending date',min_value=1,max_value=31,step=1)

if data:
    f = Data_file(data,beginning_date,ending_date)