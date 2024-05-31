# Import necessary modules
import streamlit as st
import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('railways.db')
c = conn.cursor()


# Database setup
def create_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT,
        password TEXT,
        designation TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS trains (
        train_number TEXT,
        train_name TEXT,
        start_destination TEXT,
        end_destination TEXT,
        departure_date DATE
    )""")


create_db()


# Train-related functions
def add_train(train_number, train_name, start_destination, end_destination, departure_date):
    c.execute("""
    INSERT INTO trains (train_number, train_name, start_destination, end_destination, departure_date)
    VALUES (?, ?, ?, ?, ?)""", (train_number, train_name, start_destination, end_destination, departure_date))
    conn.commit()
    create_seat_table(train_number)


def create_seat_table(train_number):
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS seats_{train_number} (
        seat_number INTEGER PRIMARY KEY,
        seat_type TEXT,
        booked INTEGER,
        passenger_name TEXT,
        passenger_age INTEGER,
        passenger_gender TEXT
    )""")

    for i in range(1, 51):
        val = categorize_seat(i)
        c.execute(f"""
        INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name,
         passenger_age, passenger_gender)
        VALUES (?, ?, ?, ?, ?, ?)""", (i, val, 0, "", 0, ""))
    conn.commit()


def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "Window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"


def allocate_next_available_seat(train_number, seat_type):
    seat_query = c.execute(f"""
    SELECT seat_number FROM seats_{train_number} 
    WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC""", (seat_type,))
    result = seat_query.fetchone()
    return result[0] if result else None


def view_seats(train_number):
    seat_query = c.execute(f"""
    SELECT seat_number, seat_type, passenger_name, passenger_age, passenger_gender, booked 
    FROM seats_{train_number} ORDER BY seat_number ASC""")
    result = seat_query.fetchall()
    if result:
        df = pd.DataFrame(result,
                          columns=["Seat Number", "Seat Type", "Passenger Name", "Passenger Age", "Passenger Gender",
                                   "Booked"])
        st.dataframe(df)


def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    seat_number = allocate_next_available_seat(train_number, seat_type)
    if seat_number:
        c.execute(f"""
        UPDATE seats_{train_number} 
        SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? 
        WHERE seat_number=?""", (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success("BOOKED SUCCESSFULLY")


def cancel_tickets(train_number, seat_number):
    c.execute(f"""
    UPDATE seats_{train_number} 
    SET booked=0, passenger_name='', passenger_age=0, passenger_gender='' 
    WHERE seat_number=?""", (seat_number,))
    conn.commit()
    st.success("CANCELLED SUCCESSFULLY")


def delete_train(train_number, departure_date):
    c.execute("DELETE FROM trains WHERE train_number=? AND departure_date=?", (train_number, departure_date))
    c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
    conn.commit()
    st.success("TRAIN DELETED SUCCESSFULLY")


# Streamlit UI functions
def train_functions():
    st.title("Train Administration")
    functions = st.sidebar.selectbox("Select Train Function",
                                     ["Add Train", "View Trains", "Book Tickets", "Cancel Tickets", "View Seats",
                                      "Delete Train"])

    if functions == "Add Train":
        st.header("Add New Train")
        with st.form(key='new_train_details'):
            train_number = st.text_input("Train Number")
            train_name = st.text_input("Train Name")
            start_destination = st.text_input("Start Destination")
            end_destination = st.text_input("End Destination")
            departure_date = st.date_input("Departure Date")
            submitted = st.form_submit_button("Add Train")
        if submitted and train_number and train_name and start_destination and end_destination and departure_date:
            add_train(train_number, train_name, start_destination, end_destination, departure_date)
            st.success("TRAIN ADDED SUCCESSFULLY")

    elif functions == "View Trains":
        st.title("View All Trains")
        train_query = c.execute("SELECT * FROM trains")
        trains = train_query.fetchall()
        if trains:
            df = pd.DataFrame(trains, columns=["Train Number", "Train Name", "Start Destination", "End Destination",
                                               "Departure Date"])
            st.table(df)
        else:
            st.info("No trains available.")

    elif functions == "Book Tickets":
        st.title("Book Train Tickets")
        with st.form(key='book_tickets_form'):
            train_number = st.text_input("Enter Train Number")
            seat_type = st.selectbox("Seat Type", ["Aisle", "Middle", "Window"])
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.number_input("Passenger Age", min_value=1)
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female"])
            submit = st.form_submit_button("Book Ticket")
        if submit and train_number and passenger_name and passenger_age and passenger_gender:
            book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

    elif functions == "Cancel Tickets":
        st.title("Cancel Train Tickets")
        with st.form(key='cancel_tickets_form'):
            train_number = st.text_input("Enter Train Number")
            seat_number = st.number_input("Enter Seat Number", min_value=1)
            submit = st.form_submit_button("Cancel Ticket")
        if submit and train_number and seat_number:
            cancel_tickets(train_number, seat_number)

    elif functions == "View Seats":
        st.title("View Seats")
        with st.form(key='view_seats_form'):
            train_number = st.text_input("Enter Train Number")
            submit = st.form_submit_button("Submit")
        if submit and train_number:
            view_seats(train_number)

    elif functions == "Delete Train":
        st.title("Delete Train")
        with st.form(key='delete_train_form'):
            train_number = st.text_input("Enter Train Number")
            departure_date = st.date_input("Enter Departure Date")
            submit = st.form_submit_button("Delete Train")
        if submit and train_number and departure_date:
            delete_train(train_number, departure_date)


# Run the train functions
train_functions()