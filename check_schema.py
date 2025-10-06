#!/usr/bin/env python3
import mysql.connector
from dictionaries import NPC_TYPES_COLUMNS

try:
    conn = mysql.connector.connect(
        host='192.168.1.105',
        user='eqemu',
        password='eqemu',
        database='peq'
    )
    cursor = conn.cursor()
    
    # Check the actual table schema
    cursor.execute('DESCRIBE npc_types')
    schema = cursor.fetchall()
    print('Actual npc_types table schema:')
    for i, row in enumerate(schema):
        print(f'  {i+1:2d}. {row[0]} ({row[1]})')
    
    print(f'\nTotal columns in table: {len(schema)}')
    
    print('\nColumns from NPC_TYPES_COLUMNS constant:')
    # Parse the constant to see individual column names
    columns_from_constant = []
    for line in NPC_TYPES_COLUMNS.strip().split('\n'):
        if line.strip():
            # Split by comma and clean up
            line_cols = [col.strip().replace('npc_types.', '') for col in line.split(',') if col.strip()]
            columns_from_constant.extend(line_cols)
    
    print(f'Expected columns from constant: {len(columns_from_constant)}')
    for i, col in enumerate(columns_from_constant):
        print(f'  {i+1:2d}. {col}')
    
    # Compare actual vs expected
    actual_columns = [row[0] for row in schema]
    print('\nColumn comparison:')
    print('Missing from constant (new columns):')
    for col in actual_columns:
        if col not in columns_from_constant:
            print(f'  + {col}')
    
    print('\nIn constant but not in table (removed columns):')
    for col in columns_from_constant:
        if col not in actual_columns:
            print(f'  - {col}')
    
    # Test the query
    print('\nTesting current query:')
    try:
        cursor.execute(f'SELECT {NPC_TYPES_COLUMNS} FROM npc_types LIMIT 1')
        result = cursor.fetchone()
        print('✓ Query executed successfully')
        print(f'  Returned {len(result) if result else 0} columns')
    except Exception as e:
        print(f'✗ Query failed: {e}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Database connection failed: {e}')
