
from baseObject import baseObject
from datetime import datetime
from experiments import experiments
from media import media
import json

class question(baseObject):
    def __init__(self):
        self.setup()
        self.valid_types = ['open-ended', 'multiple-choice', 'scale']

    def verify_new(self, n=0):
        self.errors = []

        # Validate QuestionText
        question_text = self.data[n].get('QuestionText', '').strip()
        if len(question_text) < 5:
            self.errors.append('QuestionText must be at least 5 characters long.')

        # Validate QuestionType
        question_type = self.data[n].get('QuestionType')
        if question_type not in self.valid_types:
            self.errors.append(f"QuestionType must be one of: {', '.join(self.valid_types)}")

        # Handle Choices (for multiple-choice)
        if question_type == 'multiple-choice':
            choices_raw = self.data[n].get('Choices', '').strip()
            if not choices_raw:
                self.errors.append('Choices must be provided for multiple-choice questions.')
            else:
                try:
                    # Try to load as JSON
                    parsed = json.loads(choices_raw)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        self.data[n]['Choices'] = json.dumps(parsed)
                    else:
                        self.errors.append('Choices must be a non-empty JSON list (e.g. ["Yes", "No"]).')
                except:
                    # If not JSON, assume comma-separated text
                    choices_list = [c.strip() for c in choices_raw.split(',') if c.strip()]
                    if len(choices_list) > 0:
                        self.data[n]['Choices'] = json.dumps(choices_list)
                    else:
                        self.errors.append('Choices must be a non-empty list (comma-separated or JSON).')

        # Validate ExperimentID
        experiment_id = self.data[n].get('ExperimentID')
        if not experiment_id:
            self.errors.append('ExperimentID is required.')
        else:
            exp = experiments()
            exp.getById(experiment_id)
            if len(exp.data) == 0:
                self.errors.append(f"ExperimentID {experiment_id} does not exist.")

        # Validate MediaID
        media_id = self.data[n].get('MediaID')
        if not media_id:
            self.errors.append('MediaID is required.')
        else:
            m = media()
            m.getById(media_id)
            if len(m.data) == 0:
                self.errors.append(f"MediaID {media_id} does not exist.")

        # Set CreatedTime
        self.data[n]['CreatedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return len(self.errors) == 0

    def verify_update(self, n=0):
        self.errors = []

        # Validate QuestionText
        question_text = self.data[n].get('QuestionText', '').strip()
        if question_text and len(question_text) < 5:
            self.errors.append('QuestionText must be at least 5 characters long.')

        # Validate QuestionType
        question_type = self.data[n].get('QuestionType')
        if question_type and question_type not in self.valid_types:
            self.errors.append(f"QuestionType must be one of: {', '.join(self.valid_types)}")

        # Handle Choices (for multiple-choice)
        if question_type == 'multiple-choice':
            choices_raw = self.data[n].get('Choices', '').strip()
            if not choices_raw:
                self.errors.append('Choices must be provided for multiple-choice questions.')
            else:
                try:
                    parsed = json.loads(choices_raw)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        self.data[n]['Choices'] = json.dumps(parsed)
                    else:
                        self.errors.append('Choices must be a non-empty JSON list (e.g. ["Yes", "No"]).')
                except:
                    choices_list = [c.strip() for c in choices_raw.split(',') if c.strip()]
                    if len(choices_list) > 0:
                        self.data[n]['Choices'] = json.dumps(choices_list)
                    else:
                        self.errors.append('Choices must be a non-empty list (comma-separated or JSON).')

        # Validate CreatedTime
        created_time = self.data[n].get('CreatedTime')
        if created_time:
            if isinstance(created_time, str):
                try:
                    datetime.strptime(created_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    self.errors.append('CreatedTime must be in YYYY-MM-DD HH:MM:SS format.')
            elif not isinstance(created_time, datetime):
                self.errors.append('CreatedTime must be a valid datetime or formatted string.')

        # Validate ExperimentID
        experiment_id = self.data[n].get('ExperimentID')
        if experiment_id:
            exp = experiments()
            exp.getById(experiment_id)
            if len(exp.data) == 0:
                self.errors.append(f"ExperimentID {experiment_id} does not exist.")

        # Validate MediaID
        media_id = self.data[n].get('MediaID')
        if media_id:
            m = media()
            m.getById(media_id)
            if len(m.data) == 0:
                self.errors.append(f"MediaID {media_id} does not exist.")

        return len(self.errors) == 0

    def load_choices(self):
        for row in self.data:
            if row.get('QuestionType') == 'multiple-choice':
                choices_raw = row.get('Choices', '[]')
                if isinstance(choices_raw, str):
                    try:
                        row['Choices'] = json.loads(choices_raw)
                    except Exception as e:
                        print(f"⚠️ Failed to parse choices for QuestionID {row.get('QuestionID')}: {e}")
                        row['Choices'] = []
            else:
                row['Choices'] = []
