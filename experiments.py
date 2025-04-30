from baseObject import baseObject
from datetime import datetime
import hashlib

class experiments(baseObject):
    def __init__(self):
        self.setup()

    def generate_experiment_code(self, experiment_id):
        """Generate a unique 32-character experiment code."""
        return hashlib.md5(str(experiment_id).encode()).hexdigest()[:32]

    def verify_new(self, n=0):
        """Validate and prepare a new experiment."""
        self.errors = []

        # Validate Description
        if 'Description' not in self.data[n] or len(self.data[n]['Description'].strip()) < 10:
            self.errors.append("Description must be at least 10 characters long.")

        # Validate StartDate and EndDate
        try:
            start_val = self.data[n]['StartDate']
            end_val = self.data[n]['EndDate']

            start_date = start_val if isinstance(start_val, datetime) else datetime.strptime(start_val, "%Y-%m-%d")
            end_date = end_val if isinstance(end_val, datetime) else datetime.strptime(end_val, "%Y-%m-%d")

            if start_date >= end_date:
                self.errors.append("StartDate must be before EndDate.")
        except (ValueError, KeyError):
            self.errors.append("Invalid or missing date format. Use YYYY-MM-DD.")

        # Set CreatedTime for new record
        self.data[n]['CreatedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Set UpdatedDate initially as None
        self.data[n]['UpdatedDate'] = None

        return len(self.errors) == 0

    def verify_update(self, n=0):
        """Validate and prepare an experiment for update."""
        self.errors = []

        # Validate Description
        if 'Description' not in self.data[n] or len(self.data[n]['Description'].strip()) < 10:
            self.errors.append("Description must be at least 10 characters long.")

        # Validate StartDate and EndDate
        try:
            start_val = self.data[n]['StartDate']
            end_val = self.data[n]['EndDate']

            start_date = start_val if isinstance(start_val, datetime) else datetime.strptime(start_val, "%Y-%m-%d")
            end_date = end_val if isinstance(end_val, datetime) else datetime.strptime(end_val, "%Y-%m-%d")

            if start_date >= end_date:
                self.errors.append("StartDate must be before EndDate.")
        except (ValueError, KeyError):
            self.errors.append("Invalid or missing date format. Use YYYY-MM-DD.")

        # Automatically update UpdatedDate when modifying
        self.data[n]['UpdatedDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return len(self.errors) == 0


