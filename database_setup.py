# database_setup.py
import sqlite3
from datetime import datetime, timedelta
import random

def create_database():
    """Create GPR defects database with tables"""
    conn = sqlite3.connect('gpr_defects.db')
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS repair_history')
    cursor.execute('DROP TABLE IF EXISTS measurements')
    cursor.execute('DROP TABLE IF EXISTS defects')
    cursor.execute('DROP TABLE IF EXISTS scans')
    
    # Create scans table
    cursor.execute('''
    CREATE TABLE scans (
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        road_section TEXT,
        scan_date DATE,
        file_path TEXT,
        total_length_m REAL,
        scan_quality TEXT CHECK(scan_quality IN ('excellent', 'good', 'fair', 'poor'))
    )
    ''')
    
    # Create defects table
    cursor.execute('''
    CREATE TABLE defects (
        defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER,
        defect_type TEXT CHECK(defect_type IN ('cavity', 'crack', 'pipe', 'manhole', 'delamination')),
        depth_cm REAL,
        severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
        bbox_x INTEGER,
        bbox_y INTEGER,
        bbox_width INTEGER,
        bbox_height INTEGER,
        confidence REAL,
        FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
    )
    ''')
    
    # Create measurements table
    cursor.execute('''
    CREATE TABLE measurements (
        measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        defect_id INTEGER,
        measurement_type TEXT CHECK(measurement_type IN ('length', 'width', 'area', 'volume')),
        value_cm REAL,
        calculation_method TEXT,
        measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (defect_id) REFERENCES defects(defect_id)
    )
    ''')
    
    # Create repair_history table
    cursor.execute('''
    CREATE TABLE repair_history (
        repair_id INTEGER PRIMARY KEY AUTOINCREMENT,
        defect_id INTEGER,
        repair_date DATE,
        repair_type TEXT,
        cost_usd REAL,
        contractor TEXT,
        status TEXT CHECK(status IN ('planned', 'in_progress', 'completed', 'verified')),
        FOREIGN KEY (defect_id) REFERENCES defects(defect_id)
    )
    ''')
    
    conn.commit()
    return conn

def populate_sample_data(conn):
    """Populate database with realistic sample data"""
    cursor = conn.cursor()
    
    # Korean road locations
    locations = [
        ('Gangnam-daero', 'Section A'),
        ('Gangnam-daero', 'Section B'),
        ('Teheran-ro', 'Section C'),
        ('Seocho-daero', 'Section D'),
        ('Yeongdong-daero', 'Section E')
    ]
    
    defect_types = ['cavity', 'crack', 'pipe', 'manhole', 'delamination']
    severities = ['low', 'medium', 'high', 'critical']
    qualities = ['excellent', 'good', 'fair']
    
    # Insert scans
    base_date = datetime.now() - timedelta(days=90)
    scan_ids = []
    
    print("Creating scans...")
    for i in range(15):
        location, section = random.choice(locations)
        scan_date = base_date + timedelta(days=i*6)
        cursor.execute('''
            INSERT INTO scans (location, road_section, scan_date, file_path, total_length_m, scan_quality)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            location,
            section,
            scan_date.strftime('%Y-%m-%d'),
            f'/data/gpr_scans/scan_{i+1:03d}.h5',
            round(random.uniform(100, 500), 2),
            random.choice(qualities)
        ))
        scan_ids.append(cursor.lastrowid)
    
    # Insert defects
    print("Creating defects...")
    defect_ids = []
    for scan_id in scan_ids:
        num_defects = random.randint(5, 15)
        for _ in range(num_defects):
            defect_type = random.choice(defect_types)
            
            # Realistic severity distribution
            if defect_type == 'crack':
                severity = random.choices(severities, weights=[40, 35, 20, 5])[0]
                depth = random.uniform(2, 15)
            elif defect_type == 'cavity':
                severity = random.choices(severities, weights=[10, 30, 40, 20])[0]
                depth = random.uniform(10, 50)
            else:
                severity = random.choices(severities, weights=[50, 30, 15, 5])[0]
                depth = random.uniform(5, 30)
            
            cursor.execute('''
                INSERT INTO defects (scan_id, defect_type, depth_cm, severity, 
                                   bbox_x, bbox_y, bbox_width, bbox_height, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id,
                defect_type,
                round(depth, 2),
                severity,
                random.randint(0, 800),
                random.randint(0, 600),
                random.randint(20, 200),
                random.randint(20, 200),
                round(random.uniform(0.7, 0.99), 3)
            ))
            defect_ids.append(cursor.lastrowid)
    
    # Insert measurements
    print("Creating measurements...")
    for defect_id in defect_ids:
        # Length measurement
        cursor.execute('''
            INSERT INTO measurements (defect_id, measurement_type, value_cm, calculation_method)
            VALUES (?, 'length', ?, ?)
        ''', (defect_id, round(random.uniform(10, 150), 2), random.choice(['bbox', 'skeleton'])))
        
        # Width measurement
        cursor.execute('''
            INSERT INTO measurements (defect_id, measurement_type, value_cm, calculation_method)
            VALUES (?, 'width', ?, ?)
        ''', (defect_id, round(random.uniform(5, 50), 2), 'bbox'))
    
    # Insert repair history
    print("Creating repair history...")
    for _ in range(30):
        defect_id = random.choice(defect_ids)
        repair_date = datetime.now() - timedelta(days=random.randint(0, 60))
        cursor.execute('''
            INSERT INTO repair_history (defect_id, repair_date, repair_type, cost_usd, contractor, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            defect_id,
            repair_date.strftime('%Y-%m-%d'),
            random.choice(['patching', 'full_replacement', 'monitoring', 'urgent_repair']),
            round(random.uniform(500, 15000), 2),
            random.choice(['RoadTech Inc', 'Seoul Infrastructure', 'FastRepair Co']),
            random.choice(['planned', 'in_progress', 'completed', 'verified'])
        ))
    
    conn.commit()
    
    print(f"\n✅ Database created successfully!")
    print(f"   - {len(scan_ids)} scans")
    print(f"   - {len(defect_ids)} defects")
    print(f"   - {len(defect_ids)*2} measurements")
    print(f"   - 30 repair records")

if __name__ == '__main__':
    print("🚀 Setting up GPR Defects Database...\n")
    conn = create_database()
    populate_sample_data(conn)
    conn.close()
    print("\n✅ Setup complete! Database saved as 'gpr_defects.db'")