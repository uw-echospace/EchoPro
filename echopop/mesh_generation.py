# import os
# from pathlib import Path

# import numpy as np
# import pandas as pd
# from sqlalchemy import create_engine, text

# SQL_COMMANDS["create"].format(**{"table_name": "A", "column_definitions": "B"})

# # Coordinates
# x = np.array([1, 2, 3, 4, 5])
# y = np.array([1, 2, 3, 4, 5])

# # Create the grid points
# grid_points = [(i, j, 0) for i in x for j in y]

# def initialize_grid():


# data_root_dir = Path("C:/Users/Brandyn/Documents/GitHub/EchoPro_data/")
# db_directory = data_root_dir / "database"
# # ---- Create the directory if it does not already exist
# db_directory.mkdir(parents=True, exist_ok=True)
# # ---- Complete path to `biology.db`
# db_file = db_directory / "grid.db"

# from sqlalchemy import MetaData, Table, case, create_engine, inspect, select, text, update

# engine = create_engine(f"sqlite:///{db_file}")

# # Define metadata and the table to drop
# metadata = MetaData()
# grid_table = Table('grid', metadata, autoload_with=engine)
# # Drop the table
# with engine.connect() as connection:
#     grid_table.drop(connection)
#     print("Table 'grid' has been dropped.")

# # Inspect the database
# inspector = inspect(engine)
# tables = inspector.get_table_names()
# print(tables)

# def create_table_sql(table_name, columns, primary_keys=None, index_columns=None):
#     """
#     Generate a SQL command to create a table with dynamic columns, primary keys, and indices.

#     Args:
#         table_name (str): The name of the table.
#         columns (dict): A dictionary where keys are column names and values are data types.
#         primary_keys (list, optional): List of column names to be used as primary keys.
#         index_columns (list, optional): List of column names to be indexed.

#     Returns:
#         str: The SQL command to create the table.
#     """
#     # Generate column definitions
#     column_definitions = ",\n    ".join(f"{col} {dtype}" for col, dtype in columns.items())

#     # Generate primary key definition
#     primary_key_definition = ""
#     if primary_keys:
#         primary_key_definition = f",\n    PRIMARY KEY ({', '.join(primary_keys)})"

#     # Generate index definitions
#     index_definitions = ""
#     if index_columns:
#         index_definitions = "\n".join(
#             f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{col} ON {table_name} ({col});"
#             for col in index_columns
#         )

#     # Combine all parts into the final SQL command
#     create_table_command = f"""
#     CREATE TABLE IF NOT EXISTS {table_name} (
#         {column_definitions}
#         {primary_key_definition}
#     );
#     """
#     # Return the command and any index definitions
#     return create_table_command.strip() + "\n" + index_definitions

# # Define metadata and the table to drop
# metadata = MetaData()
# grid_table = Table('grid', metadata, autoload_with=engine)
# # Drop the table
# with engine.connect() as connection:
#     grid_table.drop(connection)
#     print("Table 'grid' has been dropped.")

# check_table_exists(engine, "grid")

# with engine.connect() as connection:
#     sql_create(connection, df, table_name, primary_keys)

# # Create the table
# table_name = "grid"
# columns = {"x": "INTEGER", "y": "INTEGER", "value": "REAL"}
# primary_keys = ["x", "y"]
# index_columns = ["x", "y"]

# create_sql = create_table_sql(table_name, columns, primary_keys, index_columns)
# print("Create Table SQL:\n", create_sql)

# with engine.connect() as connection:
#     connection.execute(text(create_sql))

# inspector = inspect(engine)
# tables = inspector.get_table_names()
# print(tables)

# check_table_exists(engine, "grid")

# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)

# converted_data[0]
# check_table_exists(engine, "files_read")

# zarr_files_str = ["A", "B", "C", "D"]
# # ---- Create DataFrame
# current_files = pd.DataFrame(zarr_files_str, columns=["filepath"])

# with engine.connect() as connection:
#     sql_create(connection, table_name="files_read", df=current_files)
#     sql_insert(connection, table_name="files_read", columns=["filepath"], dataframe=current_files)

# table_name = "files_read"
# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)


# from sqlalchemy.exc import IntegrityError


# def insert_or_update(engine, table_name, columns, data, conflict_columns):
#     """
#     Insert or update data in a table.

#     Args:
#         engine (Engine): The SQLAlchemy engine instance.
#         table_name (str): The name of the table.
#         columns (list): List of column names.
#         data (list of dict): List of dictionaries containing data to insert or update.
#         conflict_columns (list): List of column names to use for conflict resolution.
#     """

#     # Prepare the SQL statement for insertion
#     column_names = ", ".join(columns)
#     placeholder = ", ".join(f":{col}" for col in columns)
#     # values_list = ", ".join(f"({', '.join(f':{col}' for col in columns)})" for _ in data)
#     values_str = ", ".join(
#         f"({', '.join(map(str, row))})"
#         for row in data
#     )


#     # Construct the SQL query
#     sql = f"""
#     INSERT INTO {table_name} ({column_names})
#     VALUES {values_str}
#     ON CONFLICT ({', '.join(conflict_columns)})
#     DO UPDATE SET {', '.join(f'{col}=excluded.{col}' for col in columns)}
#     """

#     # Flatten the list of data for execution
#     # flattened_data = [item for sublist in [[(item[col] for col in columns)] for item
# in data] for item in sublist]

#     # Execute the SQL command
#     with engine.connect() as connection:
#         try:
#             connection.execute(text(sql))
#             # connection.commit()
#             print(f"Data inserted or updated successfully in table '{table_name}'.")
#         except IntegrityError as e:
#             print(f"IntegrityError: {e}")
#         except Exception as e:
#             print(f"An error occurred: {e}")

# # Prepare data for insertion or update
# # data = [{'x': i, 'y': j, 'value': v} for i, j, v in grid_points]
# data = grid_points

# # Insert or update data
# insert_or_update(engine, table_name, columns.keys(), data, primary_keys)

# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)

# def update_specific_rows(engine, table_name, updates, conditions):
#     """
#     Update specific rows in a table based on conditions.

#     Args:
#         engine (Engine): The SQLAlchemy engine instance.
#         table_name (str): The name of the table.
#         updates (dict): Dictionary of columns and their new values to be updated.
#         conditions (dict): Dictionary of columns and their values to be used in the WHERE clause.
#     """

#     # Construct the SET clause for the update
#     set_clause = ", ".join(f"{col} = :{col}" for col in updates.keys())

#     # Construct the WHERE clause for the update
#     where_clause = " AND ".join(f"{col} = :{col}_cond" for col in conditions.keys())

#     # Construct the SQL query
#     sql = f"""
#     UPDATE {table_name}
#     SET {set_clause}
#     WHERE {where_clause}
#     """

#     # Prepare parameters for the query
#     parameters = {**updates, **{f"{col}_cond": val for col, val in conditions.items()}}

#     # Execute the SQL command
#     with engine.connect() as connection:
#         try:
#             connection.execute(text(sql), parameters)
#             print(f"Rows updated successfully in table '{table_name}'.")
#         except IntegrityError as e:
#             print(f"IntegrityError: {e}")
#         except Exception as e:
#             print(f"An error occurred: {e}")

# # Define table name
# table_name = "grid"
# # Define the table and columns
# table_name = 'grid'
# condition_columns = ['x', 'y']

# # Define the updates and conditions
# dd = {"x": np.array([1, 2, 3 , 4, 5]),"" "y": np.array([1, 2, 3 , 4, 5]), "value":
# np.array([1, 2, 3 , 4, 5]).astype(float)}
# new_data = pd.DataFrame(dd)
# new_data
# df = new_data

# kwargs = {"table_name": "grid", "columns": df.columns, "df": df}

# with engine.connect() as connection:
#     # sql_create(connection, table_name = "grid", df = df)
#     # sql_validate(connection, "grid")
#     # sql_drop(connection, "grid")
#     sql_insert(connection, table_name="grid", columns=df.columns, dataframe=df,
# id_columns=["x", "y"])


# data_tuples = [tuple(row) for row in df.itertuples(index=False)]

# all_columns = df.columns.tolist()
# if len(condition_columns) >= len(all_columns):
#     raise ValueError("The number of condition columns must be less than the number of
# columns in data.")

# # Prepare column names and conditions
# update_columns = [col for col in all_columns if col not in condition_columns]
# condition_str = " AND ".join(f"{col} = ?" for col in condition_columns)
# update_str = ", ".join(f"{col} = ?" for col in update_columns)
# data_tuples = [tuple(row) for row in df.itertuples(index=False)]
# # Generate values string for SQL command
# values_str = ", ".join(
#     f"({', '.join(map(str, row))})"
#     for row in data_tuples
# )

# # Construct the SQL query
# sql = f"""
# INSERT INTO {table_name} ({', '.join(all_columns)})
# VALUES {values_str}
# ON CONFLICT ({', '.join(condition_columns)})
# DO UPDATE SET {', '.join(f'{col} = {table_name}.{col} + excluded.{col}' for col inupdate_columns)}
# """

# # Execute the SQL command
# with engine.connect() as connection:
#     try:
#         connection.execute(text(sql))
#         connection.commit()
#         print(f"Specific rows updated successfully in table '{table_name}'.")
#     except IntegrityError as e:
#         print(f"IntegrityError: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)


# # Insert or update data
# insert_or_update(engine, table_name, columns.keys(), data, primary_keys)

# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)

# # Ensure that condition_columns match the length of data tuples minus the update column
# if len(condition_columns) != len(df.columns) - 1:
#     raise ValueError("The number of condition columns must match the number of columns in
# data minus the update column.")

# # Prepare the SQL statement for update
# update_columns = [col for col in df.columns if col not in condition_columns]
# condition_str = " AND ".join(f"{col} = ?" for col in condition_columns)
# update_str = ", ".join(f"{col} = ?" for col in update_columns)
# # Convert DataFrame rows to list of tuples
# data_tuples = [tuple(row) for row in df.itertuples(index=False)]

# # Generate a values string for the SQL command
# values_str = ", ".join(
#     f"({', '.join(map(str, row))})"
#     for row in data_tuples
# )
# # Construct the SQL query
# sql = f"""
# UPDATE {table_name}
# SET {update_str}
# WHERE {condition_str}
# """

# # Flatten the list of data for execution
# flattened_data = []
# for row in data_tuples:
#     conditions = row[:len(condition_columns)]
#     update_values = row[len(condition_columns):]
#     flattened_data.extend(conditions + update_values)

# # Execute the SQL command
# with engine.connect() as connection:
#     try:
#         connection.execute(text(sql), flattened_data)
#         print(f"Specific rows updated successfully in table '{table_name}'.")
#     except IntegrityError as e:
#         print(f"IntegrityError: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# # Execute the SQL command
# with engine.connect() as connection:
#     try:
#         connection.execute(text(sql), flattened_data)
#         print(f"Specific rows updated successfully in table '{table_name}'.")
#     except IntegrityError as e:
#         print(f"IntegrityError: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
# # Update specific rows
# update_specific_rows(engine, table_name, updates, conditions)

# # Verify the update
# sql_command = f"SELECT * FROM {table_name};"
# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# for row in rows:
#     print(row)
# # Construct the full SQL command
# sql_command = f"""
# INSERT INTO {table_name} ({columns_str})
# VALUES {values_str};
# """

# # Execute the SQL command
# with engine.connect() as connection:
#     connection.execute(text(sql_command))
#     connection.commit()

# check_table_exists(engine, "grid")

# # Define table name, columns, and data
# table_name = 'grid'
# columns = ['x', 'y', 'value']
# data = [
#     (1, 1, 1.0),
#     (2, 2, 1.5),
#     (3, 3, 2.0)
# ]

# # Prepare the columns part of the SQL statement
# columns_str = ", ".join(columns)

# # Prepare the values part of the SQL statement
# values_str = ", ".join(
#     f"({', '.join(map(str, row))})"
#     for row in data
# )


# print("Generated SQL Command:")
# print(sql_command)

# # Execute the SQL command
# with engine.connect() as connection:
#     connection.execute(text(sql_command))

# def insert_values_sql(table_name, columns, values, filter_clause=""):
#     """
#     Generate a SQL command to insert values into a table.

#     Args:
#         table_name (str): The name of the table.
#         columns (list): List of column names to be inserted.
#         values (list of tuples): List of tuples where each tuple represents a row of values
# to be inserted.
#         filter_clause (str, optional): Optional filter clause to specify conditions for insertion.

#     Returns:
#         str: The SQL command to insert values into the table.
#     """
#     # Generate column names
#     column_names = ", ".join(columns)

#     # Generate value placeholders
#     value_placeholders = ", ".join("?" * len(columns))

#     # Generate values part
#     values_part = ", ".join(f"({', '.join('?' * len(columns))})" for _ in values)

#     # Flatten the values list for insertion
#     flattened_values = [item for sublist in values for item in sublist]

#     # Create the SQL command
#     insert_command = f"""
#     INSERT INTO {table_name} ({column_names})
#     VALUES {values_part}
#     {filter_clause}
#     """
#     return insert_command.strip(), flattened_values

# # Define the values for insertion
# insert_columns = ["x", "y", "value"]
# insert_values = [(1, 1, 10.0)]

# insert_sql, insert_data = insert_values_sql(table_name, insert_columns, insert_values)
# print("Insert Values SQL:\n", insert_sql)
# print("Data:\n", insert_data)

# insrt_stmt =

# with engine.connect() as connection:
#     connection.execute(text(insert_sql), tuple(insert_data))

# # Define the values for insertion
# insert_columns = ["x", "y", "value"]
# insert_values = [(1, 1, 10.0), (2, 2, 20.0), (3, 3, 30.0)]

# # Call the function
# insert_or_update_table(engine, table_name, columns, data, conflict_columns)

# # Example usage
# table_name = "grid"
# columns = ["x", "y", "value"]
# data = [
#     (1, 1, 1.0),
#     (2, 2, 1.5),
#     (3, 3, 2.0),
# ]

# sql_command = "INSERT INTO grid (x, y, value) VALUES (:x, :y, :value)"
# test_data = [{'x': 1, 'y': 1, 'value': 1.0}]

# with engine.connect() as connection:
#     connection.execute(text(sql_command), test_data)

# # Generate the SQL command and data
# insert_stmt = insert_into_table(table_name, columns, data)

# # Print the generated SQL command (for validation)
# print("Insert SQL Command:")
# print(insert_stmt)

# # Print for validation
# print("Insert SQL Command:")
# print(insert_sql)
# print("Data:")
# print(insert_data)

# # Example execution with SQLAlchemy
# with engine.connect() as connection:
#     connection.execute(insert_stmt)

# def insert_values_sql(table_name, columns, values):
#     """
#     Generate SQL command for inserting values into a table.

#     Args:
#         table_name (str): The name of the table.
#         columns (list): List of column names.
#         values (list of tuples): List of values to insert.

#     Returns:
#         str: The SQL command to insert the values.
#         list: Flattened list of values for binding to the SQL command.
#     """
#     column_names = ", ".join(columns)
#     value_placeholders = ", ".join("?" * len(columns))
#     values_part = ", ".join(f"({value_placeholders})" for _ in values)
#     flattened_values = [item for sublist in values for item in sublist]

#     insert_command = f"""
#     INSERT INTO {table_name} ({column_names})
#     VALUES {values_part}
#     """
#     return insert_command.strip(), flattened_values

# def check_table_exists(engine, table_name):
#     """
#     Check if a table exists in the database.

#     Args:
#         engine: SQLAlchemy engine object.
#         table_name (str): The name of the table to check.

#     Returns:
#         bool: True if the table exists, False otherwise.
#     """
#     inspector = inspect(engine)
#     return table_name in inspector.get_table_names()

# with engine.connect() as connection:
#     # sql_validate(connection, "grid")
#     sql_inspect(connection)
#     sql_drop(connection, table_name)

# def select_from_table(engine, table_name, columns='*'):
#     """
#     Select data from a table.

#     Args:
#         engine: SQLAlchemy engine object.
#         table_name (str): The name of the table to select from.
#         columns (str or list): Columns to select. '*' selects all columns.

#     Returns:
#         list: List of rows returned by the query.
#     """
#     metadata = MetaData(bind=engine)
#     table = Table(table_name, metadata, autoload_with=engine)

#     if columns == '*':
#         columns = [col.name for col in table.columns]
#     elif isinstance(columns, str):
#         columns = [columns]

#     stmt = select([table.c[col] for col in columns])

#     with engine.connect() as connection:
#         result = connection.execute(stmt)
#         return result.fetchall()

# # Create table
# table_name = "grid"
# columns = {"x": "INTEGER", "y": "INTEGER", "value": "REAL"}
# primary_keys = ["x", "y"]
# index_columns = ["value"]

# create_sql = create_table_sql(table_name, columns, primary_keys, index_columns)
# print("Create Table SQL:\n", create_sql)

# with engine.connect() as connection:
#     connection.execute(create_sql)

# insert_columns = ["x", "y", "value"]
# insert_values = [(1, 1, 10.0), (2, 2, 20.0), (3, 3, 30.0)]

# # Insert data function
# def insert_values_sql(table_name, columns, values):
#     column_names = ", ".join(columns)
#     value_placeholders = ", ".join("?" * len(columns))
#     values_part = ", ".join(f"({value_placeholders})" for _ in values)

#     insert_command = f"""
#     INSERT INTO {table_name} ({column_names})
#     VALUES {values_part}
#     """
#     # Flatten the list of values into a single list
#     flattened_values = [value for sublist in values for value in sublist]

#     return insert_command.strip(), flattened_values


# table_name = 'grid'
# columns = ['x', 'y', 'value']
# data = [
#     (1, 1, 1.0),
#     (2, 2, 1.5),
#     (3, 3, 2.0)
# ]

# # Prepare the columns part of the SQL statement
# columns_str = ", ".join(columns)

# # Prepare the values part of the SQL statement
# values_str = ", ".join(
#     f"({', '.join(map(str, row))})"
#     for row in data
# )

# # Construct the full SQL command
# sql_command = f"""
# INSERT INTO {table_name} ({columns_str})
# VALUES {values_str};
# """

# # Execute the SQL command
# with engine.connect() as connection:
#     connection.execute(text(sql_command))

# sql_command = f"SELECT * FROM {table_name};"

# with engine.connect() as connection:
#     result = connection.execute(text(sql_command))
#     rows = result.fetchall()

# print(f"Data in table {table_name}:")
# for row in rows:
#     print(row)
# # Construct the full SQL command
# sql_command = f"""
# INSERT INTO {table_name} ({columns_str})
# VALUES {values_str};
# """


# insert_sql, insert_data = insert_values_sql(table_name, insert_columns, insert_values)
# print("Insert Values SQL:\n", insert_sql)
# print("Insert Data:\n", insert_data)

# with engine.connect() as connection:
#     connection.execute(insert_sql, [insert_data])

# # Check table existence
# exists = check_table_exists(engine, table_name)
# print(f"Table '{table_name}' exists: {exists}")

# # Select data from table
# data = select_from_table(engine, table_name, insert_columns)
# print(f"Data from '{table_name}':")
# for row in data:
#     print(row)


# create_sql = create_table_sql(table_name, columns, primary_keys, index_columns)
# print("Create Table SQL:\n", create_sql)

# # Define the values for insertion
# insert_columns = ["x", "y", "value"]
# insert_values = [(1, 1, 10.0)]

# insert_sql, insert_data = insert_values_sql(table_name, insert_columns, insert_values)
# print("Insert Values SQL:\n", insert_sql)
# print("Data:\n", insert_data)

# # Example usage
# table_name = "grid"
# columns = {
#     "x": "INTEGER",
#     "y": "INTEGER",
#     "value": "REAL"
# }
# primary_keys = ["x", "y"]
# index_columns = ["value"]

# sql_command = create_table_sql(table_name, columns, primary_keys, index_columns)
# print(sql_command)

# # Create the table
# create_table_sql = """
# CREATE TABLE IF NOT EXISTS grid (
#     x INTEGER,
#     y INTEGER,
#     value REAL,
#     PRIMARY KEY (x, y)
# );
# """

# # Insert grid points
# insert_values = ", ".join(f"({i}, {j}, {v})" for i, j, v in grid_points)
# insert_sql = f"""
# INSERT INTO grid (x, y, value) VALUES {insert_values};
# """

# # Connect to the database and execute the commands
# with engine.connect() as connection:
#     try:
#         # Create table if it does not exist
#         connection.execute(text(create_table_sql))
#         # Insert grid points
#         connection.execute(text(insert_sql))
#         connection.commit()
#         print("Grid points successfully inserted.")
#     except Exception as e:
#         print(f"An error occurred: {e}")


# engine = create_engine(f"sqlite:///{db_file}")
# metadata = MetaData()
# grid_table = Table('grid', metadata, autoload_with=engine)
# # Read existing grid values from the database into a DataFrame
# with engine.connect() as connection:
#     select_stmt = select(grid_table.c.x, grid_table.c.y, grid_table.c.value)
#     result = connection.execute(select_stmt)
#     existing_data = pd.DataFrame(result.fetchall(), columns=['x', 'y', 'value'])

# # Coordinates to update
# update_coords = {(1,1), (2,2), (3,3), (4,4), (5,5)}

# # Create a dictionary for fast lookup
# update_dict = {(i, j): 1.0 for i, j in update_coords}

# # Update the grid_points with new values where applicable
# updated_grid_points = [
#     (i, j, update_dict.get((i, j), value))
#     for i, j, value in grid_points
# ]

# # Convert the list of tuples to a DataFrame
# df_updated_grid_points = pd.DataFrame(updated_grid_points, columns=['x', 'y', 'value'])

# # Print the DataFrame
# print(df_updated_grid_points)

# # Merge existing and updated data to find differences
# merged_data = pd.merge(existing_data, df_updated_grid_points,
# on=['x', 'y'], suffixes=('_existing', '_updated'))
# differences = merged_data[merged_data['value_existing'] != merged_data['value_updated']]

# # Assuming 'differences' is your DataFrame with updated values
# # Create a dictionary for batch updating
# update_dict = differences.set_index(['x', 'y'])['value_updated'].to_dict()

# # Generate the SQLAlchemy update statement
# update_stmt = update(grid_table).where(
#     grid_table.c.x.in_(update_dict.keys())
# ).values({
#     grid_table.c.value: update_dict.get((grid_table.c.x, grid_table.c.y), grid_table.c.value)
# })

# # Create the CASE statement
# case_stmt = case(
#     {
#         (grid_table.c.x == x) & (grid_table.c.y == y): value
#         for (x, y), value in update_dict.items()
#     },
#     else_=grid_table.c.value
# )

# # Convert the DataFrame into a dictionary of case statements
# case_stmt = case(
#     [(grid_table.c.x == x) & (grid_table.c.y == y), value]
#     for (x, y), value in update_dict.items()
# )

# # Create the case statement
# case_stmt = case(
#     { (x, y): value for (x, y), value in update_dict.items() },
#     value=grid_table.c.x,  # Assuming `x` is the column being compared
#     else_=grid_table.c.value
# )

# case_stmt = case(
#     {
#         (x, y): value
#         for (x, y), value in update_dict.items()
#     },
#     value=grid_table.c.x,
#     else_=grid_table.c.value
# )

# # Create the case statement
# # Create a CASE statement using a dictionary
# case_stmt = case(
#     {
#         (grid_table.c.x == x) & (grid_table.c.y == y): value
#         for (x, y), value in update_dict.items()
#     },
#     else_=grid_table.c.value
# )
# case_stmt = case(
#     {((grid_table.c.x == x) & (grid_table.c.y == y)): value
#      for (x, y), value in update_dict.items()},
#     else_=grid_table.c.value
# )
# print("Case Statement:", str(case_stmt.compile(engine,
# compile_kwargs={"literal_binds": True})))


# # Create the update statement
# update_stmt = (
#     update(grid_table).
#     where(grid_table.c.value != case_stmt).
#     values(value=case_stmt)
# )

# print("Update Statement:", str(update_stmt.compile(engine,
# compile_kwargs={"literal_binds": True})))


# # Print the SQL for each update
# for (x, y), value in update_dict.items():
#     update_stmt = (
#         update(grid_table)
#         .where((grid_table.c.x == x) & (grid_table.c.y == y))
#         .values(value=value)
#     )
#     # Print the SQL statement with literal values for debugging
#     print("Update Statement:", str(update_stmt.compile(engine,
# compile_kwargs={"literal_binds": True})))

#     # Execute the update statement
#     with engine.connect() as connection:
#         result = connection.execute(update_stmt)
#         print(f"Updated {result.rowcount} entries for coordinates ({x}, {y}).")

# # Execute the update
# with engine.connect() as connection:
#     result = connection.execute(update_stmt)
#     print(f"Updated {result.rowcount} entries.")

# engine.dispose()

# engine = create_engine(f"sqlite:///{db_file}")
# metadata = MetaData()
# grid_table = Table('grid', metadata, autoload_with=engine)
# # Verify the updated rows
# select_stmt = select(grid_table)

# with engine.connect() as connection:
#     result = connection.execute(select_stmt)
#     rows = result.fetchall()

# for row in rows:
#     print(row)

# # Define your SQLite engine and metadata
# engine = create_engine(F'sqlite:///{db_file}')
# metadata = MetaData()

# # Reflect the grid table
# grid_table = Table('grid', metadata, autoload_with=engine)

# # Define your update dictionary
# update_dict = {(1, 1): 1.0, (2, 2): 1.0, (3, 3): 1.0, (4, 4): 1.0, (5, 5): 1.0}

# # Execute updates
# # with engine.connect() as connection:
# connection = engine.connect()
# # for (x, y), value in update_dict.items():
# (x,y) = (1, 1)
# value = update_dict[(1,1)]

# update_stmt = (
#     update(grid_table)
#     .where((grid_table.c.x == x) & (grid_table.c.y == y))
#     .values(value=value)
# )
# # Print the SQL statement for debugging
# print("Executing Update Statement:", str(update_stmt.compile(engine,
# compile_kwargs={"literal_binds": True})))

# # Execute the update statement
# result = connection.execute(update_stmt)
# print(f"Updated {result.rowcount} entries for coordinates ({x}, {y}).")
# connection.close()

# select_stmt = select(grid_table.c.x)

# # Execute the SELECT statement
# with engine.connect() as connection:
#     result = connection.execute(select_stmt)
#     x_values = result.fetchall()

# type(x_values[0])

# select_stmt = select(grid_table.c.y)

# # Execute the SELECT statement
# with engine.connect() as connection:
#     result = connection.execute(select_stmt)
#     y_values = result.fetchall()

# select_stmt = select(grid_table.c.value)

# # Execute the SELECT statement
# with engine.connect() as connection:
#     result = connection.execute(select_stmt)
#     values = result.fetchall()

# case_stmt = case(
#     *[(grid_table.c.x == x) & (grid_table.c.y == y, value)
#       for (x, y), value in update_dict.items()],
#     else_=grid_table.c.value
# )

# update_dict = {(1, 2): 1.0, (3, 2): 1.0, (1, 5): 1.0, (4, 5): 1.0, (3, 5): 4.0}

# with engine.connect() as connection:
#     # Select all values to check the current state
#     result = connection.execute(select(grid_table.c.x, grid_table.c.y, grid_table.c.value))
#     current_values = result.fetchall()
#     print("Current Values:", current_values)

# with engine.connect() as connection:
#     with connection.begin():  # Begin a transaction
#         for (x, y), value in update_dict.items():
#             stmt = (
#                 update(grid_table)
#                 .where((grid_table.c.x == x) & (grid_table.c.y == y))
#                 .values(value=grid_table.c.value + value)
#             )
#             connection.execute(stmt)

# with engine.connect() as connection:
#     # Re-select to check the updated state
#     result = connection.execute(select(grid_table.c.x, grid_table.c.y, grid_table.c.value))
#     updated_values = result.fetchall()
#     print("Updated Values:", updated_values)


# # Confirm the updates
# with engine.connect() as connection:
#     select_stmt = select([grid_table])
#     result = connection.execute(select_stmt)
#     rows = result.fetchall()

# # Print all rows to verify updates
# print("Database contents after update:")
# for row in rows:
#     print(row)


# # Construct the update statement
# update_stmt = (
#     update(grid_table)
#     .values(value=case_stmt)
#     .where(grid_table.c.value != case_stmt)
# )

# # Create a SELECT statement to fetch all rows from the grid_table
# select_stmt = select(grid_table)

# # Execute the SELECT statement and fetch results
# with engine.connect() as connection:
#     result = connection.execute(select_stmt)
#     rows = result.fetchall()

# # Print or inspect the fetched rows
# for row in rows:
#     print(row)

# # Create the update statement
# update_stmt = (
#     update(grid_table)
#     .where(grid_table.c.value != case_stmt)
#     .values(value=case_stmt)
# )

# # Execute the update
# with engine.connect() as connection:
#     result = connection.execute(update_stmt)
#     print(f"Updated {result.rowcount} entries.")

# case(
#     [
#         ((grid_table.c.x == x) & (grid_table.c.y == y), value)
#         for (x, y), value in update_dict.items()
#     ],
#     else_=grid_table.c.value
# )

# # Create a case statement for conditional update
# case_statements = {
#     (x, y): case(
#         [(grid_table.c.x == x) & (grid_table.c.y == y, value)],
#         else_=grid_table.c.value
#     )
#     for (x, y), value in update_dict.items()
# }


# # Define SQL command to select all data from the grid table
# select_sql = "SELECT * FROM grid;"

# # Connect to the database and execute the query
# with engine.connect() as connection:
#     try:
#         # Execute the select command
#         result = connection.execute(text(select_sql))
#         # Fetch all rows from the result
#         rows = result.fetchall()
#         # Print the results
#         print("Data in grid table:")
#         for row in rows:
#             print(row)
#     except Exception as e:
#         print("An error occurred: {}".format(e))

# # Coordinates to update
# update_coords = {(1,1), (2,2), (3,3), (4,4), (5,5)}

# # Create a copy of grid_points and update specific coordinates
# updated_grid_points = [
#     (i, j, 1.0) if (i, j) in update_coords else (i, j, value)
#     for i, j, value in grid_points
# ]

# # Retrieve current data from the database
# with engine.connect() as connection:
#     result = connection.execute(text("SELECT x, y, value FROM grid;"))
#     current_data = result.fetchall()

# # Convert to a dictionary for easy comparison
# current_values = {(x, y): value for x, y, value in current_data}

# # Convert updated_grid_points to a dictionary
# updated_values = {(i, j): value for i, j, value in updated_grid_points}

# # Find differences
# differences = [
#     (i, j, value)
#     for i, j, value in updated_grid_points
#     if (i, j) in updated_values and (i, j) not in current_values or
#     (i, j) in current_values and current_values[(i, j)] != value
# ]

# # Update differing values in the database
# with engine.connect() as connection:
#     for i, j, value in differences:
#         connection.execute(
#             text(f"UPDATE grid SET value = {value} WHERE x = {i} AND y = {j}"),
#         )
#     print(f"Updated {len(differences)} entries.")

# # Step 8: Read the table into Python
# with engine.connect() as connection:
#     # Query to select all rows from the table
#     result = connection.execute(text("SELECT x, y, value FROM grid;"))
#     df = pd.DataFrame(result.fetchall(), columns=['x', 'y', 'value'])

# # Print the DataFrame to validate the changes
# print(df)

# # Check current values
# with engine.connect() as connection:
#     result = connection.execute(text("SELECT x, y, value FROM grid;"))
#     current_values = {(row[0], row[1]): row[2] for row in result.fetchall()}

# print("Current grid points in database:")
# for row in current_values.items():
#     print(row)

# print("Updated grid points with changes:")
# for row in updated_grid_points:
#     print(row)

# # Determine differences
# differences = [
#     (i, j, value)
#     for i, j, value in updated_grid_points
#     if (i, j) in current_values and current_values[(i, j)] != value
# ]

# print(f"Differences to update: {differences}")

# # Step 6: Update the database with INSERT OR REPLACE
# with engine.connect() as connection:
#     with connection.begin():  # Ensure transactions are committed
#         for i, j, value in updated_grid_points:
#             sql = """
#             INSERT OR REPLACE INTO grid (x, y, value)
#             VALUES (:x, :y, :value)
#             """
#             print(f"Executing SQL: {sql} with values: x={i}, y={j}, value={value}")
#             connection.execute(
#                 text(sql),
#                 {"x": i, "y": j, "value": value}
#             )
#         print(f"Updated entries with INSERT OR REPLACE.")

# # Step 8: Read the table into Python
# with engine.connect() as connection:
#     result = connection.execute(text("SELECT x, y, value FROM grid;"))
#     rows = result.fetchall()
#     df = pd.DataFrame(rows, columns=['x', 'y', 'value'])

# # Print the DataFrame to validate the changes
# print("Updated table data:")
# print(df)


# engine.dispose()

# # Check if the file exists and then remove it
# if db_file.exists():
#     db_file.unlink()
#     print(f"Deleted the file: {db_file}")
# else:
#     print(f"The file does not exist: {db_file}")

# with engine.connect() as connection:
#     connection.execute(text("""
#     CREATE TABLE IF NOT EXISTS grid (
#         x INTEGER,
#         y INTEGER,
#         value REAL,
#         PRIMARY KEY (x, y)
#     );
#     """))

#     connection.execute(text("""
#     INSERT OR REPLACE INTO grid (x, y, value) VALUES
#     (1, 1, 0), (1, 2, 0), (1, 3, 0), (1, 4, 0), (1, 5, 0),
#     (2, 1, 0), (2, 2, 0), (2, 3, 0), (2, 4, 0), (2, 5, 0),
#     (3, 1, 0), (3, 2, 0), (3, 3, 0), (3, 4, 0), (3, 5, 0),
#     (4, 1, 0), (4, 2, 0), (4, 3, 0), (4, 4, 0), (4, 5, 0),
#     (5, 1, 0), (5, 2, 0), (5, 3, 0), (5, 4, 0), (5, 5, 0);
#     """))

#     # Insert initial values (0) into the grid table
#     values = ",".join(["({}, {}, {})".format(i, j, 0) for i, j, _ in grid_points])
#     connection.execute(text("INSERT INTO grid (x, y, value) VALUES {values};"
# .format(values=values)))

#     # Commit
#     connection.commit()

#     # Verify data insertion
#     result = connection.execute(text("SELECT * FROM grid;"))
#     rows = result.fetchall()
#     print("Data in grid table:", rows)

#     connection.execute(text("""
#     INSERT INTO grid (x, y, value) VALUES
#     """ + ",".join(["({}, {}, {})".format(i, j, 0) for i, j, _ in grid_points]) + ";"))

# engine.dispose()


#     result = connection.execute(text("SELECT * FROM grid;"))
#     rows = result.fetchall()
#     print("Data in grid table:", rows)

# with engine.connect() as connection:
#     result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
#     print(result.fetchall())

# with engine.connect() as connection:
#     # Describe the table schema
#     result = connection.execute(text("PRAGMA table_info(grid);"))
#     columns = result.fetchall()
#     print("Table schema:", columns)

# with engine.connect() as connection:
#     result = connection.execute(text("SELECT * FROM grid;"))
#     rows = result.fetchall()
#     for row in rows:
#         print(row)

# SQL(db_file, command="select")


# import geopandas as gpd
# import geopy
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import pyproj
# import shapely.geometry
# from geopy.distance import distance
# from shapely.geometry import Point, Polygon, box
# from shapely.ops import unary_union

# from echopop.spatial.projection import utm_string_generator, wgs84_to_utm
# from echopop.survey import Survey

# survey = Survey( init_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_files/ini
# tialization_config.yml" ,
#                  survey_year_config_path = "C:/Users/Brandyn/Documents/GitHub/echopop/config_fil
# es/survey_year_2019_config.yml" )


# grid_settings = file_configuration["geospatial"]["griddify"]
# # lat_min = grid_settings["bounds"]["latitude"][0]
# lat_min = 33.75
# # lat_max = grid_settings["bounds"]["latitude"][1]
# lat_max = 55.50
# # lon_min = grid_settings["bounds"]["longitude"][0]
# lon_min = -134.25
# lon_max = grid_settings["bounds"]["longitude"][1]

# projection = file_configuration["geospatial"]["projection"]

# utm_code = utm_string_generator((lon_max + lon_min)/2, (lat_max + lat_min)/2)
# utm_num = int(utm_code)
# utm_str = f"epsg:{utm_num}"

# biology_data = filtered_biology_output

# from sqlalchemy import Engine, create_engine, inspect, text

# root_dir = file_configuration["data_root_dir"]
# db_directory = Path(root_dir) / "database"
# db_directory.mkdir(parents=True, exist_ok=True)
# db_file = db_directory / "biology.db"
# # Create the engine with the full path
# engine = create_engine(f'sqlite:///{db_file}')

# SQL_COMMANDS = {
#     "create": "CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});",
#     "check": "SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';",
#     "drop": "DROP TABLE IF EXISTS {table_name};",
#     "select": "SELECT {columns} FROM {table_name};",
#     "index": "CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})",
#     # "insert": "INSERT INTO {table_name} ({columns});",
#     "insert": """
#         INSERT INTO {table_name} ({columns})
#         SELECT {columns}
#         FROM (SELECT VALUES {values} FROM (VALUES {value_placeholder})) AS source ({columns})
#         {filter_clause};
#         """,
#     "inspect": None,
# }

# SQL_DTYPES = {
#     'int32': 'INTEGER',
#     'int64': 'INTEGER',
#     'float64': 'FLOAT',
#     'bool': 'BOOLEAN',
#     'datetime64[ns]': 'DATETIME',
#     'object': 'TEXT'
# }

# def SQL(db_file: str, command: str, **kwargs):

#     # Create engine from `db_file` string
#     engine = create_engine(f"sqlite:///{db_file}")

#     # Format `columns`, if there are any and more than 1
#     if "columns" in kwargs.keys():
#         if isinstance(kwargs["columns"], list):
#             kwargs["columns"] = ", ".join(kwargs["columns"])
#     else:
#         kwargs["columns"] = "*"

#     # Format `columns`, if there are any and more than 1
#     # if "filter_columns" in kwargs.keys():
#     #     # ---- Store the value for later
#     #     kwargs["filter_columns_store"] = kwargs["filter_columns"]
#     #     if isinstance(kwargs["filter_columns"], list):
#     #         kwargs["filter_columns"] = ", ".join(kwargs["filter_columns"])

#     # Run the command
#     try:
#         with engine.connect() as connection:
#             # ---- SELECT
#             if command == "select":
#                 return pd.read_sql(text(SQL_COMMANDS[command].format(**kwargs)), con=connection)
#             # ---- CREATE
#             elif command == "create":
#                 # ---- Extract dataframe
#                 df_to_add = kwargs["dataframe"]
#                 # ---- Check whether the table already exists or not
#                 table_exists = (
#                     connection.execute(text(SQL_COMMANDS["check"].format(**kwargs))).fetchone()
#                 )
#                 # ---- If it doesn't, pre-allocate the table
#                 if table_exists is None:
#                     # ---- Get column definitions as a string
#                     column_def_dict = {
#                         col: SQL_DTYPES.get(str(dtype), 'TEXT')
#                         for col, dtype in zip(df_to_add.columns, df_to_add.dtypes)
#                     }
#                     # ---- Convert to a single string
#                     kwargs["column_definitions"] = (
#                         ", ".join([f"{col} {dtype}" for col, dtype in column_def_dict.items()])
#                     )
#                     # ---- Create table
#                     connection.execute(text(SQL_COMMANDS["create"].format(**kwargs)))
#             # ---- REPLACE
#             elif command == "replace":
#                 # ---- Extract dataframe
#                 df_to_add = kwargs["dataframe"]
#                 # ---- Replace current
#                 df_to_add.to_sql(name=kwargs["table_name"],
#                                  con=connection,
#                                  if_exists="replace", index=False)

#             # ---- INSERT
#             elif command == "insert":
#                 # ---- Extract dataframe
#                 df_to_add = kwargs["dataframe"]
#                 # ---- Check if
#                 # table_exists = (
#                 #     connection.execute(text(SQL_COMMANDS["check"].format(**kwargs))).fetchone()
#                 # )
#                 # tables = SQL(db_file, "inspect")
#                 # ---- If it doesn't, pre-allocate the table
#                 # if kwargs["table_name"] not in tables and "filter_columns" in kwargs.keys():
#                 df_to_add.to_sql(name=kwargs["table_name"],
#                                     con=connection,
#                                     if_exists="append", index=False)
#                 # else:
#                     #     # ---- Format `filter_columns` command if present
#                     # if "filter_columns" in kwargs.keys():
#                     #     # ---- Fetch table
#                     #     fetch_table = (
#                     #         connection.execute(text(
#                     #             ("SELECT DISTINCT {filter_columns} FROM {table_name}")
#                     #             .format(**kwargs))
#                     #         )
#                     #     )
#                     #     # ---- Format the SQL data into a DataFrame
#                     #     fetched_df = pd.DataFrame(fetch_table.fetchall(),
# columns=fetch_table.keys())
#                     #     # ---- Create an index tuples
#                     #     index_tuples = (
#                     #         set(fetched_df[kwargs["filter_columns_store"]]
#                     #             .itertuples(index=False, name=None))
#                     #     )
#                     #     # ---- Filter the dataframe
#                     #     filtered_df = (
#                     #         df_to_add[
#                     #             ~df_to_add[fetched_df.columns].apply(tuple, axis=1)
#                     #             .isin(index_tuples)
#                     #             ]
#                     #     )
#                     #     # ---- Insert the data
#                     #     filtered_df.to_sql(name=kwargs["table_name"],
#                     #                         con=connection,
#                     #                         if_exists="append", index=False)
#                     # else:
#                     # df_to_add.to_sql(name=kwargs["table_name"],
#                     #                 con=connection,
#                     #                 if_exists="append", index=False)
#             # ---- INSPECT
#             elif command == "inspect":
#                 return inspect(engine).get_table_names()
#             else:
#                 connection.execute(text(SQL_COMMANDS[command].format(**kwargs)))
#     finally:
#         # ---- Dispose of the engine to release any resources being pooled/used
#         engine.dispose()

# _ = SQL(db_file, "drop", table_name="catch_df")
# _ = SQL(db_file, "drop", table_name="specimen_df")
# _ = SQL(db_file, "drop", table_name="length_df")
# _ = SQL(db_file, "drop", table_name="files_read")

# _ = SQL(db_file, "insert", table_name="files_read", dataframe=current_files)
# current = SQL(db_file, "select", table_name="files_read", columns="filepath")
# current


# # Get acoustic directory and initialization settings
# # ---- Files
# biology_file_settings = file_configuration["input_directories"]["biological"]
# # ---- General settings
# biology_analysis_settings = file_configuration["biology"]

# # Get the file-specific settings, datatypes, columns, etc.
# # ---- Get defined columns and datatypes from `LIVE_INPUT_FILE_CONFIG_MAP`
# biology_config_map = LIVE_INPUT_FILE_CONFIG_MAP["biology"]
# # ---- Extract the expected file name ID's
# biology_file_ids = biology_file_settings["file_name_formats"]
# # ---- Extract all of the file ids
# biology_config_ids = list(biology_file_ids.keys())
# # ---- Initialize the dictionary that will define this key in the `input` attribute
# biology_output = {f"{key}_df": pd.DataFrame() for key in biology_config_ids}
# # ---- Initialize the SQL dictionary
# sql_biology_output = {f"{key}_df": pd.DataFrame() for key in biology_config_ids}

# # Create full filepath
# biology_directory_path = (
#     Path(file_configuration["data_root_dir"]) / biology_file_settings["directory"]
# )
# # ---- Directory check
# directory_existence = biology_directory_path.exists()
# # ---- Error evaluation (if applicable)
# if not directory_existence:
#     raise FileNotFoundError(
#         f"The acoustic data directory [{biology_directory_path}] does not exist."
#     )
# # ---- Get the defined file extension
# file_extension = biology_file_settings["extension"]
# # ---- Create Path.glob generator object
# file_path_obj = biology_directory_path.glob(f"*{'.'+file_extension}")
# #---- Create list of `*.csv`` files
# csv_files = list(file_path_obj)
# # ---- Ensure files exist or raise error otherwise
# if len(csv_files) < 1:
#     raise FileNotFoundError(
#         f"No `*.csv` files found in [{biology_directory_path}]!"
#     )
# else:
#     # ---- Create Path to SQL database file
#     db_directory = Path(file_configuration["data_root_dir"]) / "database"
#     # ---- Create the directory if it does not already exist
#     db_directory.mkdir(parents=True, exist_ok=True)
#     # ---- Complete path to `biology.db`
#     db_file = db_directory / "biology.db"
#     # ---- Query the external SQL database to see if the file tracking table exists
#     tables = SQL(db_file, "inspect")
#     # ---- Create a list of string-formatted Path names
#     csv_files_str = [str(file) for file in csv_files]
#     # ---- Create DataFrame
#     current_files = pd.DataFrame(csv_files_str, columns=["filepath"])
#     # ---- Create if it is missing and then advance `csv_files`
#     if "files_read" not in tables:
#         # ---- Insert into the SQL database file
#         _ = SQL(db_file, "insert", table_name="files_read", columns="filepath",
#                     dataframe=current_files)
#         # ---- Create empty list for later comparison
#         new_files = []
#     else:
#         # ---- Pull already processed filenames
#         previous_files = SQL(db_file, "select", table_name="files_read")
#         # ---- Compare against the current filelist
#         new_files = (
#             [file for file in csv_files_str if file not in set(previous_files["filepath"])]
#         )
#         # ---- Create a DataFrame for the new files
#         new_files_df = pd.DataFrame(new_files, columns=["filepath"])
#         # ---- Insert into the SQL database file
#         _ = SQL(db_file, "insert", table_name="files_read", dataframe=new_files_df)

# # Iterate through each of the file ids and read in the data
# for id in list(biology_file_ids.keys()):
#     # ---- Extract the specific config mapping for this tag/id
#     sub_config_map = biology_config_map[id]
#     # ---- Drop the `{FIELD_ID}` tag identifier
#     file_id_format = re.sub(r'\{FILE_ID:([^}]+)\}', r'\1', biology_file_ids[id])
#     # ---- Replace all other tags with `*` placeholders
#     file_id_format = re.sub(r"\{[^{}]+\}", "*", file_id_format)
#     # ---- Create Path object with the generalized format
#     subfile_path_obj = biology_directory_path.glob(f"{file_id_format}.{file_extension}")
#     # ---- List all files that match this pattern
#     subcsv_files_str = [str(file) for file in list(subfile_path_obj)]
#     # ---- Filter for only new files
#     subset_files = set(subcsv_files_str).intersection(set(new_files))
#     # ---- Pull from SQL database, if applicable
#     if f"{id}_df" in tables:
#         # ---- SELECT
#         sql_df = SQL(db_file, "select", table_name=f"{id}_df", columns="*")
#         # ---- Concatenate to the dictionary
#         sql_biology_output[f"{id}_df"] = pd.concat([biology_output[f"{id}_df"], sql_df])
#     # ---- Add data files not stored in SQL database
#     if len(subset_files) > 0 or len(subset_files)== 0 and f"{id}_df" not in tables:
#         if len(subset_files) > 0:
#             file_list = subset_files
#         else:
#             file_list = subcsv_files_str
#         # ---- Create a list of relevant dataframes
#         sub_df_lst = [read_biology_csv(Path(file), biology_file_ids[id], sub_config_map)
#                         for file in file_list]
#         # ---- Concatenate into a single DataFrame
#         sub_df = pd.concat(sub_df_lst, ignore_index=True)
#         # ---- Concatenate to the dictionary DataFrame
#         biology_output[f"{id}_df"] = pd.concat([biology_output[f"{id}_df"], sub_df])

# # Get contrasts used for filtering the dataset
# # ---- Species
# species_filter = file_configuration["species"]["number_code"]
# # ---- Trawl partition information
# trawl_filter = biology_analysis_settings["catch"]["partition"]
# # ---- Apply the filter
# filtered_biology_output = {
#     key: df[
#         (df['species_id'] == species_filter if 'species_id' in df.columns else True) &
#         (df['trawl_partition'].str.lower() == trawl_filter if 'trawl_partition' in df.columns
# else True)
#     ]
#     for key, df in biology_output.items() if isinstance(df, pd.DataFrame) and not df.empty
# }

# # Update the SQL database
# for table_name, df in filtered_biology_output.items():
#     # ---- Update
#     _ = SQL(db_file, "insert", table_name=table_name, columns="*",
#             dataframe=df)

# # Combine the two datasets
# merged_output = {
#     key: pd.concat([
#         sql_biology_output.get(key, pd.DataFrame()),
#         filtered_biology_output.get(key, pd.DataFrame())
#     ]).drop_duplicates().reset_index(drop=True)
#     for key in set(sql_biology_output) | set(filtered_biology_output)
# }
# # ---- Return output
# merged_output

# coordinate_metadata.attrs[]

# SQL(biology_db, command="drop", table_name="catch_df")
# SQL(biology_db, command="drop", table_name="specimen_df")
# SQL(biology_db, command="drop", table_name="length_df")
# SQL(biology_db, command="drop", table_name="files_read")
# _ = SQL(db_file=db_file, command="create", table_name="files_read", columns="filepath")
# tables = SQL(db_file, "inspect")
# tables
# current = SQL(db_file, "select", table_name="files_read", columns=["filepath"])
# current

# SQL(db_file, "select", table_name="catch_df", columns="*")
# new_files_df = pd.DataFrame(csv_files_str, columns=['file_path'])
# _ = SQL("insert", engine, table_name="files_read",dataframe=new_files_df)
# current = SQL("select", engine, table_name="csv_files_read", columns="file_path")
# current
# for table_name, df in biology_data.items():
#     df.to_sql(table_name, con=engine, if_exists='append', index=False)
# command = "read"
# engine = create_engine(f'sqlite:///{db_file}')
# table_name = "files_read"
# columns = "file_path"

# kwargs = {
#     "table_name": table_name,
#     "columns": columns,
# }

# zarr_data_ds["depth"].diff(dim="depth")

# prc_nasc_df.groupby(["longitude", "latitude"])

# from pandas.core.groupby import DataFrameGroupBy


# def estimate_echometrics(acoustic_data_df: pd.DataFrame):

#     # Create copy
#     acoustic_df = acoustic_data_df.copy().reset_index(drop=True)

#     # Pre-compute the change in depth
#     acoustic_df["dz"] = acoustic_df["depth"].diff()

#     # Initialize echometrics dictionary
#     echometrics = {}

#     # Compute the metrics center-of-mass
#     if acoustic_df["NASC"].sum() == 0.0:
#         echometrics.update({
#             "n_layers": 0,
#             "mean_Sv": -999,
#             "max_Sv": -999,
#             "nasc_db": np.nan,
#             "center_of_mass": np.nan,
#             "dispersion": np.nan,
#             "evenness": np.nan,
#             "aggregation": np.nan,
#             "occupied_area": 0.0,
#         })
#     else:

#         # Compute the number of layers
#         echometrics.update({
#             "n_layers": acoustic_df["depth"][acoustic_df["NASC"] > 0.0].size
#         })

#         # Compute ABC
#         # ---- Convert NASC to ABC
#         acoustic_df["ABC"] = acoustic_df["NASC"] / (4 * np.pi * 1852 ** 2)
#         # ---- Estimate mean Sv
#         echometrics.update({
#             "mean_Sv": 10.0 * np.log10(acoustic_df["ABC"].sum() / acoustic_df["depth"].max())
#         })
#         # --- Estimate max Sv (i.e. )
#         echometrics.update({
#             "max_Sv": 10 * np.log10(acoustic_df["ABC"].max()
#                                     / acoustic_df.loc[np.argmax(acoustic_df["ABC"]), "dz"])
#         })

#         # Compute (acoustic) abundance
#         echometrics.update({
#             "nasc_db": 10 * np.log10(acoustic_df["ABC"].sum())
#         })

#         # Compute center of mass
#         echometrics.update({
#             "center_of_mass": (
#                 (acoustic_df["depth"] * acoustic_df["NASC"]).sum()
#                 / (acoustic_df["NASC"]).sum()
#             )
#         })

#         # Compute the dispersion
#         echometrics.update({
#             "dispersion": (
#                 ((acoustic_df["depth"] - echometrics["center_of_mass"]) ** 2
#                 * acoustic_df["NASC"]).sum() / (acoustic_df["NASC"]).sum()
#             )
#         })

#         # Compute the evenness
#         echometrics.update({
#             "evenness": (acoustic_df["NASC"] **2).sum() / ((acoustic_df["NASC"]).sum()) ** 2
#         })

#         # Compute the index of aggregation
#         echometrics.update({
#             "aggregation": 1 / echometrics["evenness"]
#         })

#         # Get the occupied area
#         echometrics.update({
#             "occupied_area": (
#                 acoustic_df["dz"][acoustic_df["ABC"] > 0.0].sum() / acoustic_df["depth"].max()
#             )
#         })

#     # Return the dictionary
#     return echometrics

# def integrate_nasc(acoustic_data_df: pd.DataFrame, echometrics: bool = True):

#     # Vertically integrate PRC NASC
#     nasc_dict = {"nasc": acoustic_data_df["NASC"].sum()}

#     # Horizontally concatenate `echometrics`, if `True`
#     if echometrics:
#         # ---- Compute values
#         # NOTE: This uses NASC instead of linear `sv`
#         echometrics_dict = estimate_echometrics(acoustic_data_df)
#         # ---- Merge
#         nasc_dict.update(echometrics_dict)

#     # Convert `nasc_dict` to a DataFrame and return the output
#     return pd.Series(nasc_dict)

# def process_group(group):
#     result = integrate_nasc(group, echometrics=True)
#     result = result.reset_index(drop=True)
#     # Concatenate the result back to the original group for alignment
#     group = group.reset_index(drop=True)
#     combined = pd.concat([group, result], axis=1)
#     return combined

# acoustic_data_df = acoustic_data["prc_nasc_df"]


# rc_nasc_df[prc_nasc_df["distance"] == 0.0]
# acoustic_data_df = mek[mek["distance"] == 0.0]
# pd.DataFrame(nasc_dict, index=[0]).reset_index(drop=True).unstack()
# nasc_data_df = (
#     prc_nasc_df.groupby(["longitude", "latitude", "ping_time"])
#     .apply(lambda group: integrate_nasc(group, echometrics=False), include_groups=False)
#     .reset_index()
# )


# kwargs = {
#     "table_name": "csv_files_read",
#     "columns": "file_path",
#     "dataframe": new_files_df
# }

# current_process = psutil.Process()
# import logging

# # Create a session
# Session = sessionmaker(bind=engine)
# session = Session()

# # Perform database operations
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# logger.info("Performing database operations")

# # Create a session
# Session = sessionmaker(bind=engine)
# session = Session()

# # Perform database operations
# logger.info("Performing database operations")

# # Close the session
# session.close()
# logger.info("Session closed")

# # Dispose the engine
# engine.dispose()
# logger.info("Engine disposed")

# # Force garbage collection
# import gc

# gc.collect()
# logger.info("Garbage collection performed")

# import psutil

# pid = psutil.Process().pid
# process = psutil.Process(pid)
# open_files = process.open_files()
# db_path = r'C:\Users\Brandyn\Documents\GitHub\EchoPro_data\live_2019_files\database\biology.db'

# # Check if the file is still in use
# for file in open_files:
#     if db_path in file.path:
#         logger.info(f"File {db_path} is still in use.")
#     else:
#         logger.info(f"File {db_path} is not in use.")

# # Define the SQL to drop the table
# drop_table_sql = "DROP TABLE IF EXISTS csv_files_read;"
# # Execute the drop table SQL
# with engine.connect() as connection:
#     _ = connection.execute(text(drop_table_sql))

# import sqlite3

# if os.path.exists(db_path):
#     conn = sqlite3.connect(db_path)
#     conn.close()
#     # Force the file to be removed
#     try:
#         os.remove(db_path)
#         print(f"Database file {db_path} has been deleted.")
#     except PermissionError:
#         print(f"Failed to delete {db_path}. The file is still in use.")

# create_table_sql = """
# CREATE TABLE IF NOT EXISTS csv_files_read (
#     file_path TEXT UNIQUE
# );
# """
# # Execute the create table SQL
# with engine.connect() as connection:
#     _ = connection.execute(text(create_table_sql))

# root_directory =  Path(root_dir)
# dataset = "biology"

# # Convert to strings
# csv_files_str = [str(file) for file in csv_files]

# existing_files_df = pd.read_sql('SELECT file_path FROM csv_files_read', con=engine)
# existing_files_set = set(existing_files_df['file_path'])
# # Filter out duplicates from the csv_files list
# new_files = [file for file in csv_files_str if file not in existing_files_set]
# # Insert only new file paths into the SQL table
# if new_files:
#     new_files_df = pd.DataFrame(new_files, columns=['file_path'])
#     _ = new_files_df.to_sql('csv_files_read', con=engine, if_exists='append', index=False)


# with engine.connect() as conn:
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS csv_files_read (
#             file_path TEXT UNIQUE
#         )
#     """)

# csv_files
# files_df.to_sql('csv_files_read', con=engine, if_exists='append', index=False)
# file_name_format = biology_file_ids[id]
# def compile_filename_format(file_name_format: str):

#     # Create a copy of `file_name_format`
#     regex_pattern = file_name_format

#     # Iterate through the keys from `LIVE_FILE_FORMAT_MAP` to format a regex pattern
#     for key, value in LIVE_FILE_FORMAT_MAP.items():
#         regex_pattern = regex_pattern.replace(f"{{{key}}}", value["expression"])
#     # ---- Replace the `FILE_ID` tag
#     regex_pattern = re.sub(r'\{FILE_ID:(.+?)\}', r'(?P<FILE_ID>\1)', regex_pattern)

#     # Compile the regex pattern and return the output
#     return re.compile(regex_pattern)

# from sqlalchemy.orm import sessionmaker

# Session = sessionmaker(bind=engine)
# session = Session()
# session.close()
# engine.pool.status()
# # Dispose the engine to close all connections
# engine.dispose()
# import gc

# gc.collect()
# import psutil

# dbapi_conn = engine.raw_connection()
# dbapi_conn.close()
# # Get the process ID of the current process
# pid = psutil.Process().pid

# # List all open files for the current process
# process = psutil.Process(pid)
# open_files = process.open_files()

# for file in open_files:
#     print(file.path)


# pattern = filename_format
# config_settings = sub_config_map
# regex_pattern = pattern

# # Replace patterns based on LIVE_FILE_FORMAT_MAP
# for key, value in LIVE_FILE_FORMAT_MAP.items():
#     regex_pattern = regex_pattern.replace(f'{{{key}}}', value['expression'])
# regex_pattern = re.sub(r'\{FILE_ID:(.+?)\}', r'(?P<FILE_ID>\1)', regex_pattern)
# new_pattern = compile_filename_format(regex_pattern)
# match_obj = new_pattern.search(file.name)
# # Get substring components as a list
# filename_substrings = re.findall(r'\{([^:}]+)(?::[^}]+)?}', pattern)
# valid_tags = list(set(["HAUL", "SPECIES_CODE"]).intersection(set(filename_substrings)))

# for i in valid_tags:
#     matched_key = LIVE_FILE_FORMAT_MAP[i]
#     df[matched_key["name"]] = matched_key["dtype"](match_obj.group(i))


# # Assign the data as new columns to the DataFrame
# for key, value in data_to_add.items():
#     df[key] = value

# for i in valid_tags:
#     matched_key = LIVE_FILE_FORMAT_MAP[i]
#     df[matched_key["name"]] = matched_key["dtype"](match_obj.group(i))
# biology_analysis_settings
# species_id_value = 22500
# trawl_partition_value = 'Codend'  # Adjust as needed
# {
#     key: df[
#         (('species_id' not in df.columns) or (df['species_id'] == species_id_value)) &
#         (('trawl_partition' not in df.columns) or (df['trawl_partition'] ==
# trawl_partition_value))
#     ]
#     for key, df in biology_output.items() if isinstance(df, pd.DataFrame)
# }

# (match_obj.group(i)).astype(matched_key["dtype"])
# pattern = '{DATE:YYYYMM}_{HAUL}_{FILE_ID:catch_perc}'
# modified_pattern = re.sub(r'\{FILE_ID:(.+?)\}', r'\1', pattern)
# # Create the regex pattern
# regex_pattern = modified_pattern.replace('{', '(?P<').replace('}', '>.+?)')
# re.compile(regex_pattern)

# modified_pattern = re.sub(r'\{FILE_ID:(.+?)\}', r'\1', pattern)

# # Create the regex pattern
# regex_pattern = modified_pattern.replace('{', '(?P<').replace('}', '>.+?)')
# compile_filename_format(regex_pattern)
# # Regular expression to capture values inside the curly braces
# regex = r'\{([^:}]+):([^}]+)\}'

# # Find all matches
# matches = re.findall(regex, modified_pattern)

# # Get substring components as a list
# filename_substrings = re.findall(r'\{([^:}]+)(?::[^}]+)?}', pattern)

# pattern_changed = pattern.replace("FILE_ID:", "")

# # Compilte the filename regular expression format
# compiled_regex = compile_filename_format(pattern_changed)

# file_id_tag = pattern.split('{FILE_ID:')[1].split('}')[0]

#  # Get the file name and produce a `re.Match` object
# match_obj = compiled_regex.search(file.name)


# def read_biology_csv(file: Path, pattern: re.Pattern, config_settings: dict):

#     # Get the file name and produce a `re.Match` object
#     match_obj = pattern.search(file.name)

#     # Read in the `*.csv` file
#     df = pd.read_csv(file, usecols=list(config_settings["dtypes"].keys()))

#     # Validate the dataframe
#     # ---- Check for any missing columns
#     missing_columns = (
#         [key for key in config_settings["dtypes"].keys() if key not in df.columns]
#     )
#     # ---- Raise Error, if needed
#     if missing_columns:
#         raise ValueError(
#             f"The following columns are missing from [{file}]: {', '.join(missing_columns)}!"
#         )
#     # ---- Ensure the correct datatypes
#     df_validated = df.astype(config_settings["dtypes"])

#     # Replace column names and drop
#     df_validated = df_validated.rename(columns=config_settings["names"])

#     # Get the haul number and add the the dataframe
#     # ---- Extract the haul number and convert to an integer
#     haul_num = int(match_obj.group("HAUL"))
#     # ---- Add the column
#     df_validated["haul_num"] = haul_num

#     # Return the resulting DataFrame
#     return df_validated

# boundary_dict = griddify_definitions["bounds"]

# import geopandas as gpd
# import numpy as np
# import pandas as pd
# from geopy.distance import distance

# from echopop.spatial.projection import utm_string_generator

# ##
# grid_settings["grid_resolution"]["x"] = 50
# grid_settings["grid_resolution"]["y"] = 50
# lat_step = distance(nautical=grid_settings["grid_resolution"]["x"]).meters
# lon_step = distance(nautical=grid_settings["grid_resolution"]["y"]).meters

# # CREATE BOUNDING
# bound_df = pd.DataFrame({
#     "lon": np.array([lon_min, lon_max, lon_max, lon_min, lon_min]),
#     "lat": np.array([lat_min, lat_min, lat_max, lat_max, lat_min])
# })

# bound_gdf = gpd.GeoDataFrame(
#     data=bound_df,
#     geometry=gpd.points_from_xy(bound_df["lon"], bound_df["lat"]),
#     crs = projection
# )
# import shapely.geometry

# from echopop.spatial.projection import utm_string_generator

# utm_string_generator(-117.0, 33.75)
# bound_gdf.total_bounds
# # Convert to UTM
# bound_utm = bound_gdf.to_crs(utm_num)
# bound_utm.total_bounds
# y_step = lat_step
# x_step = lon_step
# # bound_utm = bound_gdf
# # y_step = grid_settings["grid_resolution"]["y"] * 1852 / 110574
# # x_step = grid_settings["grid_resolution"]["x"] * 1852 / 60.0

# xmin, ymin, xmax, ymax = bound_utm.total_bounds

# # Get number of cells
# n_x_cells = int(np.ceil((xmax - xmin) / x_step))
# n_y_cells = int(np.ceil((ymax - ymin) / y_step))

# import pyproj

# # create the cells in a loop
# # grid_cells = []
# # for x0 in np.arange(xmin, xmax, x_step):
# #     for y0 in np.arange(ymin, ymax, y_step):
# #         # bounds
# #         utm_zone = utm_string_generator(x0, y0)
# #         proj = pyproj.Proj(f"epsg:{utm_code}")
# #         x1 = x0-x_step
# #         y1 = y0+y_step
# #         grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

# grid_cells = []
# for y0 in np.arange(ymin, ymax, y_step):

#     # x_step = grid_settings["grid_resolution"]["x"] * 1852 / (1852 * 60 * np.cos(np.radians(y0)))

#     for x0 in np.arange(xmin, xmax, x_step):
#         # bounds
#         # utm_zone = utm_string_generator(x0, y0)
#         # proj = pyproj.Proj(f"epsg:{utm_code}")
#         # x1, y1 = proj(x0, y0)
#         # x2, y2 = proj(x0 - x_step, y0 + y_step)
#         # grid_cells.append(box(x1, y1, x2, y2))
#         x1 = x0-x_step
#         y1 = y0+y_step
#         grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

# cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs=utm_code)
# cells_gdf.shape
# n_x_cells * n_y_cells
# # cells_gdf = gpd.GeoDataFrame(grid_cells, columns=["geometry"])
# cells_gdf.total_bounds
# cells_gdf.to_crs(projection).total_bounds
# from shapely.geometry import mapping
# from shapely.validation import make_valid

# ########
# world = gpd.read_file("C:/Users/Brandyn/Documents/GitHub/EchoPro_data/live_2019_files/coastline/
# ne_10m_land/ne_10m_land.shp")
# bb_orig = box(lon_min, lat_min, lon_max, lat_max)
# boundary_box = box(lon_min - 5, lat_min - 5, lon_max + 5, lat_max + 5)
# world_orig = gpd.clip(world, box(lon_min-1, lat_min-1, lon_max+1, lat_max+1))
# world_clipped_latlon = gpd.clip(world, boundary_box)
# world_clipped = gpd.clip(world, boundary_box).to_crs(utm_code)

# world_utm = world.to_crs(utm_code)
# world_utm = world_utm[~world_utm.is_empty]

# bbox_latlon = box(lon_min, lat_min, lon_max, lat_max)

# gpd.GeoDataFrame(geometry=[bbox_latlon], crs=projection).to_crs(utm_code)

# bbox_utm = bound_utm.total_bounds

# buffer = [-lon_step * 1.01, -lat_step * 1.01, lon_step * 1.01, lat_step * 1.01]
# array_buffer = bbox_utm + buffer
# array_names = ["minx", "miny", "maxx", "maxy"]
# buffered = dict(zip(array_names, array_buffer))
# buffer_boundary = box(**buffered)
# # box(array_buffer[0], array_buffer[1], array_buffer[2], array_buffer[3])
# # buffer_boundary = buffer_boundary.to_crs(world_utm.crs)

# buffer_boundary_gdf = gpd.GeoDataFrame(geometry=[buffer_boundary], crs=world_utm.crs)
# # Replace with the correct EPSG code
# bb_orig_gdf = gpd.GeoDataFrame(geometry=[bb_orig], crs=projection)
# # sub_clipped = gpd.clip(world_utm, buffer_boundary)
# # sub_clipped = gpd.clip(world_utm, bbox_utm)

# from datetime import datetime

# import geopandas as gpd
# import matplotlib.cm as cm
# import matplotlib.colors as colors
# import matplotlib.dates as mdates
# import matplotlib.pyplot as plt
# import numpy as np
# from matplotlib.colors import ListedColormap
# from shapely import wkt

# # fig, ax = plt.subplots(figsize=(10, 10))
# # # Plot the buffer_boundary
# # world.plot(ax=ax, linewidth=2, color='gray')
# # buffer_boundary_gdf.to_crs(projection).plot(ax=ax, facecolor='none', edgecolor='blue')
# # bb_orig_gdf.plot(ax=ax, facecolor='none', edgecolor='red')
# # plt.xlim(lon_min-3, lon_max+3)
# # plt.ylim(lat_min-3, lat_max+3)
# # plt.show()
# from echopop.live.sql_methods import SQL

# db_filepath = realtime_survey.config["database"]["grid"]
# survey_db = realtime_survey.config["database"]["acoustics"]
# grid_df = SQL(db_filepath, "select", table_name="grid_df")
# # grid_df[grid_df.abundance > 0]
# grid_df[grid_df.abundance > 1e10]
# # grid_df[grid_df.abundance > 0]
# coast_df = SQL(db_filepath, "select", table_name="coastline_df")
# survey_df = SQL(survey_db, "select", table_name="survey_data_df")

# # def parse_datetime(date_str):
# #     # List of possible formats
# #     formats = [
# #         '%Y-%m-%d %H:%M:%S.%f',  # With fractional seconds
# #         '%Y-%m-%d %H:%M:%S',     # Without fractional seconds
# #         '%Y-%m-%dT%H:%M:%S.%f',  # ISO 8601 format with fractional seconds
# #         '%Y-%m-%dT%H:%M:%S'      # ISO 8601 format without fractional seconds
# #     ]

# #     for fmt in formats:
# #         try:
# #             return pd.to_datetime(date_str, format=fmt)
# #         except (ValueError, TypeError):
# #             continue  # Try the next format

# #     return pd.NaT  # Return NaT if no formats match

# # survey_df["ping_time"] = survey_df["ping_time"].apply(parse_datetime)

# # pd.to_datetime(survey_df["ping_time"], format='%Y-%m-%d %H:%M:%S.%f', errors="coerce")

# # fig, ax = plt.subplots(figsize=(5, 8))
# # ax.scatter(survey_df.ping_time, survey_df.nasc)
# # plt.ylabel("NASC")
# # # ax.xaxis.set_major_locator(mdates.DayLocator(5, 10, 15))
# # plt.show()


# # times = np.arange(np.datetime64('2001-01-02'),
# #                   np.datetime64('2002-02-03'), np.timedelta64(75, 'm'))
# # y = np.random.randn(len(times))
# # survey_df[(survey_df.nasc > 0) & (survey_df.nasc < 1e5)]["nasc"].mean()
# # survey_df[(survey_df.nasc > 0) & (survey_df.nasc > 1e5)]["nasc"].mean()

# # fig, ax = plt.subplots()
# # ax.plot(times, y)
# # survey_df[(survey_df.number_density > 0) & (survey_df.x == 21)]
# # # a = self.input["acoustics"]["prc_nasc_df"]
# # # survey_df[(survey_df.x) == 24 & (survey_df.y == 13)]

# grid_df["geometry"] = grid_df["geometry"].apply(wkt.loads)
# coast_df["geometry"] = coast_df["geometry"].apply(wkt.loads)

# projection = realtime_survey.config["geospatial"]["projection"]

# grid_gdf = gpd.GeoDataFrame(grid_df, geometry="geometry", crs=projection)
# grid_gdf_1 = grid_gdf[grid_gdf.abundance > 0]
# coast_gdf = gpd.GeoDataFrame(coast_df, geometry="geometry", crs=projection)

# lims = grid_gdf.total_bounds
# # nu = dataset_gdf[(dataset_gdf.stratum_x == 25) & (dataset_gdf.stratum_y == 11)]
# # dataset_gdf.stratum_x.max()
# # # np.linspace(1, 1, len(np.arange(xmin, xmax+x_step, x_step))-1)

# # # np.arange(1, len(np.arange(xmin, xmax+x_step, x_step)))
# # pd.cut(
# #     nu["x"],
# #     np.arange(xmin, xmax, x_step),
# #     right = False,
# #     labels = np.arange(1, len(np.arange(xmin, xmax, x_step))),
# # ).astype(int) - 1
# # grid_gdf["x"] =  grid_gdf["x"] - 1

# # fig, ax = plt.subplots(figsize=(5, 8))
# # grid_gdf.plot(ax=ax, edgecolor="gainsboro", color="white", linewidth=0.5, legend=False)
# # plt.plot(dataset_gdf.longitude, dataset_gdf.latitude, linewidth=1, color='black')
# # plt.plot(nu.longitude, nu.latitude, linewidth=1, color="red")
# # # Calculate centroids and plot text
# # for idx, row in grid_gdf.iterrows():
# #     centroid = row.geometry.centroid
# #     var = f"{row.x}-{row.y}"
# #     ax.annotate(var, xy=(centroid.x, centroid.y),
# #                 xytext=(0,0), fontsize=8,
# #                 textcoords="offset points",
# #                 ha='center', va='center', color='black')
# # plt.tight_layout()
# # plt.margins(0, 0)
# # coast_gdf.plot(ax=ax, linewidth=1.2, color='gray', edgecolor="black")
# # plt.xlim(lims[0]*1.005, lims[2]*1.01)
# # plt.ylim(lims[1]*0.98, lims[3]*1.005)
# # plt.show()


# variable = "abundance"
# VARIABLE_MAP = {
#     "number_density_mean": {
#         "name": "Mean number density",
#         "units": "fish $\\mathregular{nmi^{-2}}$"
#     },
#     "biomass_density_mean": {
#         "name": "Mean biomass density",
#         "units": "kg $\\mathregular{nmi^{-2}}$"
#     },
#     "biomass": {
#         "name": "Biomass",
#         "units": "kg"
#     },
#     "abundance": {
#         "name": "Abundance",
#         "units": "$\\it{N}$"
#     }
# }

# viridis = plt.colormaps.get_cmap('viridis').resampled(1024)
# newcolors = viridis(np.linspace(0, 1, 1024))[::-1]
# white = np.array([1, 1, 1, 1])
# newcolors[0, :] = white
# custom_cmap = ListedColormap(newcolors)
# # Check the minimum and maximum values for normalization


# fig, ax = plt.subplots(figsize=(5, 8))
# grid_gdf.plot(ax=ax, edgecolor="gainsboro", color="white", linewidth=0.5, legend=False)
# grid_gdf_1.plot(ax=ax, column=variable, edgecolor="black", linewidth=2, cmap=custom_cmap,
# legend=False, norm=norm)
# plt.scatter(survey_df["longitude"], survey_df["latitude"], linewidth=0.5, color="black")
# vmin = grid_gdf[variable][grid_gdf[variable] > 0.0].min()
# vmax = grid_gdf[variable].max()
# norm = colors.Normalize(vmin=0, vmax=vmax, clip=False)
# # norm = colors.Normalize(vmin=grid_gdf[variable][grid_gdf[variable] > 0.0].min(),
# vmax=grid_gdf[variable].max())
# # cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=custom_cmap), ax=ax,
# orientation="horizontal", shrink=0.5)
# cbar = plt.colorbar(cm.ScalarMappable(cmap=custom_cmap, norm=norm), ax=ax,
# orientation="horizontal", shrink=0.5)
# cbar.set_label(f"{VARIABLE_MAP[variable]["name"]} ({VARIABLE_MAP[variable]["units"]})",
#                fontsize=12, labelpad=10, loc='center')
# cbar.ax.xaxis.set_label_position('top')
# cbar.ax.xaxis.set_ticks_position('top')
# plt.tight_layout()
# plt.margins(0,0)
# # grid_gdf_1.plot(ax=ax, linewidth=1.5, color="black")
# coast_gdf.plot(ax=ax, linewidth=1.2, color='gray', edgecolor="black")
# plt.xlim(lims[0]*1.005, lims[2]*1.01)
# plt.ylim(lims[1]*0.98, lims[3]*1.005)
# plt.xlabel(u'Longitude (\u00B0E)')
# plt.ylabel(u'Latitude (\u00B0N)')
# plt.show()


# co = SQL(db_filepath, "select", table_name="coastline_df")
# co["geometry"] = co["geometry"].apply(wkt.loads)
# co_gdf = gpd.GeoDataFrame(co, geometry="geometry", crs=projection)


# test["geometry"].apply(wkt.loads)
# clipped_cells_latlon["geometry"]
# len(bbox_latlon.exterior.coords)
# len(buffer_boundary.exterior.coords)

# # world_clipped_latlon = gpd.clip(world_utm, buffer_boundary).to_crs(projection)
# world_clipped_latlon
# ########
# cells_clipped = cells_gdf["geometry"].difference(world_clipped.geometry.union_all())
# .to_frame("geometry")
# # cells_clipped = cells_gdf["geometry"].difference(world_clipped_latlon.geometry.union_all())
# .to_frame("geometry")
# cell_colors = cells_clipped.area / (lat_step * lon_step)
# # cell_colors = cells_clipped.to_crs({"proj": "cea"}).area / 46300.00000000001**2
# cells_clipped['cell_colors'] = cell_colors
# # ---> back to epsg lat/long
# cells_latlon = cells_clipped.to_crs(projection)
# cells_latlon_clipped = gpd.clip(cells_latlon, bb_orig_gdf)
# cell_colors_clipped = cells_latlon_clipped.to_crs(utm_code).area / (lat_step * lon_step)
# # cell_colors = cells_clipped.to_crs({"proj": "cea"}).area / 46300.00000000001**2
# cells_latlon_clipped['cell_colors'] = cell_colors_clipped
# ########
# from shapely.geometry import LineString, Point, shape

# nasc_df = survey.input["acoustics"]["nasc_df"]
# nasc_gdf = gpd.GeoDataFrame(data=nasc_df, geometry=gpd.points_from_xy(nasc_df["longitude"],
# nasc_df["latitude"]), crs=projection)
# geo_df = nasc_gdf.groupby(["transect_num"])['geometry'].apply(lambda x: LineString(x.tolist()))
# .to_frame("geometry").set_crs(projection)
# custom_crs = '+proj=epsg:4326 +lat_ts=0 +lat_0=0 +lon_0=-180 +x_0=0 +y_0=0 +datum=WGS84 +units=m
# +no_defs +type=crs'
# cells_latlon_clipped.to_crs(custom_crs).crs
# import matplotlib.cm as cm
# import matplotlib.colors as colors

# ########
# import sqlalchemy as sqla

# cells_transformed = cells_latlon.to_crs(utm_code)
# lims = cells_transformed.total_bounds

# fig, ax = plt.subplots(figsize=(10, 10))
# # cells_clipped.plot(ax=ax, column="cell_colors", edgecolor="black", cmap="viridis", legend=True)
# # cells_clipped.plot.hexbin()
# cells_latlon.to_crs(utm_code).plot(ax=ax, column="cell_colors", edgecolor="black", cmap="viridis",

#                                    legend=False)
# # cells_latlon.plot(ax=ax, column="cell_colors", edgecolor="black", cmap="viridis", legend=False)
# # cells_latlon_clipped.plot(ax=ax, column="cell_colors", edgecolor="black", cmap="viridis",
# # legend=False)
# # cells_clipped.plot(ax=ax, column="cell_colors", edgecolor="black", cmap="viridis", legend=True)
# # cells_gdf.plot(ax=ax, facecolor="none", edgecolor="black")
# norm = colors.Normalize(vmin=cells_latlon["cell_colors"].min(),
#                         vmax=cells_latlon["cell_colors"].max())
# cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap="viridis"), ax=ax,
# orientation="horizontal",
#                     shrink=0.5)
# cbar.set_label("Normalized grid area (50x50 nmi)", fontsize=12, labelpad=10, loc='center')
# cbar.ax.xaxis.set_label_position('top')
# cbar.ax.xaxis.set_ticks_position('top')
# geo_df.reset_index().to_crs(utm_code).plot(ax=ax, color="red")
# # geo_df.reset_index().plot(ax=ax, color="red")
# # plt.plot(ax=ax, nasc_df["longitude"], nasc_df["latitude"], color="red")
# ax.margins(0.00, 0.00)
# world_orig.to_crs(utm_code).plot(ax=ax, linewidth=1.2, color='gray', edgecolor="black")
# # world_orig.plot(ax=ax, linewidth=1.2, color='gray', edgecolor="black")
# # bb_orig_gdf.to_crs(utm_code).plot(ax=ax, facecolor='none', edgecolor='red')
# plt.xlim(lims[0]*1.02, lims[2]*1.01)
# # ax.set_yticks([4e6, 5e6, 6e6])
# # ax.set_yticklabels(["4000", "5000", "6000"], fontsize=10)
# plt.ylim(lims[1]*0.98, lims[3]*1.005)
# ax.set_yticks([4e6, 5e6, 6e6])
# ax.set_yticklabels(["4000", "5000", "6000"], fontsize=10)
# plt.xlabel("Eastings (km)")
# plt.ylabel("Northings (km)")
# # plt.xlabel("Longitude (°E)")
# # ax.set_xticks([-135, -130, -125, -120])
# # plt.ylabel("Latitude (°N)")
# ax.set_xticks([-600e3, -400e3, -200e3, 0, 200e3, 400e3, 600e3, 800e3])
# ax.set_xticklabels(["-600", "-400", "-200", "0", "200", "400", "600", "800"], fontsize=10)
# # Adding the colorbar title
# # cax = fig.get_axes()[1]  # Assuming the colorbar is the second axis
# # cax.set_ylabel("Normalized grid area (25x25 nmi)")  # Setting the title of the colorbar
# plt.tight_layout()
# plt.show()
