from baseObject import baseObject
from datetime import datetime
from questions import question  # to get QuestionType

class responses(baseObject):
    def __init__(self):
        self.setup()

    def verify_new(self, n=0):
        self.errors = []

        # Validate UserID
        if not self.data[n].get('UserID'):
            self.errors.append('UserID is required.')

        # Validate QuestionID
        if not self.data[n].get('QuestionID'):
            self.errors.append('QuestionID is required.')

        # Validate Answer
        answer = self.data[n].get('Answer')
        if answer is None or str(answer).strip() == '':
            self.errors.append('Answer cannot be empty.')

        # Validate Question exists and apply scale-specific rules
        question_id = self.data[n].get('QuestionID')
        if question_id:
            q = question()
            q.getById(question_id)
            if len(q.data) > 0:
                q_type = q.data[0].get('QuestionType')

                if q_type == 'scale':
                    try:
                        val = int(answer)
                        if val < 1 or val > 5:
                            self.errors.append('Answer must be a number between 1 and 5 for scale questions.')
                    except ValueError:
                        self.errors.append('Answer must be a number between 1 and 5 for scale questions.')
                # Add more type-based rules here if needed (e.g., multiple-choice validation)

            else:
                self.errors.append(f"QuestionID {question_id} does not exist.")

        # Set CreatedTime
        self.data[n]['CreatedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return len(self.errors) == 0

    def verify_update(self, n=0):
        self.errors = []

        # Validate Answer
        if 'Answer' in self.data[n]:
            answer = self.data[n]['Answer']
            if answer is None or str(answer).strip() == '':
                self.errors.append('Answer cannot be empty.')

        # Optional: Validate CreatedTime format
        if 'CreatedTime' in self.data[n]:
            try:
                datetime.strptime(self.data[n]['CreatedTime'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                self.errors.append('CreatedTime must be in YYYY-MM-DD HH:MM:SS format.')

        return len(self.errors) == 0
