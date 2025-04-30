from baseObject import baseObject
from datetime import datetime
from experiments import experiments  # For validating foreign key
import os

class media(baseObject):
    def __init__(self):
        self.setup()
        self.valid_types = ['car', 'truck', 'motorcycle']
        self.valid_extensions = ['.mp3', '.wav']

    def verify_new(self, n=0):
        self.errors = []

        # Validate FilePath
        filepath = self.data[n].get('FilePath', '').strip()
        if not filepath:
            self.errors.append('FilePath is required.')
        else:
            # Check if extension is valid
            _, ext = os.path.splitext(filepath)
            if ext.lower() not in self.valid_extensions:
                self.errors.append(f"Unsupported file format. Allowed: {', '.join(self.valid_extensions)}")

            # Check for duplicates
            if self.is_duplicate_filepath(filepath):
                self.errors.append('A media file with this FilePath already exists.')

        # Validate AutomobileType
        if self.data[n].get('AutomobileType') not in self.valid_types:
            self.errors.append(f"AutomobileType must be one of: {', '.join(self.valid_types)}")

        # # Validate Duration
        # try:
        #     duration = float(self.data[n]['Duration'])
        #     if duration <= 0:
        #         self.errors.append('Duration must be a positive number (in seconds).')
        # except Exception:
        #     self.errors.append('Duration must be a number (in seconds).')
        
        duration_raw = self.data[n].get('Duration', '').strip()

        if duration_raw == '':
            self.data[n]['Duration'] = None  # Let it be NULL in DB
        else:
            try:
                duration = float(duration_raw)
                if duration <= 0:
                    self.errors.append('Duration must be a positive number (in seconds).')
                else:
                    self.data[n]['Duration'] = duration  # Save cleaned value
            except Exception:
                self.errors.append('Duration must be a number (in seconds).')

        
        
        
        
        
        
        
        # Set CreatedTime
        self.data[n]['CreatedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate ExperimentID
        if not self.data[n].get('ExperimentID'):
            self.errors.append('ExperimentID is required.')
        else:
            exp = experiments()
            exp.getById(self.data[n]['ExperimentID'])
            if len(exp.data) == 0:
                self.errors.append(f"ExperimentID {self.data[n]['ExperimentID']} does not exist.")

        return len(self.errors) == 0

    def verify_update(self, n=0):
        self.errors = []

        # Optional FilePath check
        if 'FilePath' in self.data[n]:
            filepath = self.data[n]['FilePath'].strip()
            if not filepath:
                self.errors.append('FilePath cannot be empty.')
            else:
                _, ext = os.path.splitext(filepath)
                if ext.lower() not in self.valid_extensions:
                    self.errors.append(f"Unsupported file format. Allowed: {', '.join(self.valid_extensions)}")

        # Validate AutomobileType
        if 'AutomobileType' in self.data[n]:
            if self.data[n]['AutomobileType'] not in self.valid_types:
                self.errors.append(f"AutomobileType must be one of: {', '.join(self.valid_types)}")

        # Validate Duration
        if 'Duration' in self.data[n]:
            try:
                duration = float(self.data[n]['Duration'])
                if duration <= 0:
                    self.errors.append('Duration must be a positive number (in seconds).')
            except Exception:
                self.errors.append('Duration must be a number (in seconds).')

        # Validate CreatedTime
        if 'CreatedTime' in self.data[n]:
            try:
                datetime.strptime(self.data[n]['CreatedTime'], '%Y-%m-%d %H:%M:%S')
            except Exception:
                self.errors.append('CreatedTime must be in YYYY-MM-DD HH:MM:SS format.')

        # Validate ExperimentID
        if 'ExperimentID' in self.data[n]:
            exp = experiments()
            exp.getById(self.data[n]['ExperimentID'])
            if len(exp.data) == 0:
                self.errors.append(f"ExperimentID {self.data[n]['ExperimentID']} does not exist.")

        return len(self.errors) == 0

    def is_duplicate_filepath(self, filepath):
        sql = "SELECT * FROM mm_media WHERE FilePath = %s"
        self.cur.execute(sql, (filepath,))
        return self.cur.fetchone() is not None

    def get_by_experiment(self, experiment_id):
        sql = "SELECT * FROM mm_media WHERE ExperimentID = %s"
        self.cur.execute(sql, (experiment_id,))
        self.data = self.cur.fetchall()
