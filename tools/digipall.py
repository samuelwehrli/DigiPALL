# icons: https://www.dicebear.com/styles

from streamlit_chat import message
from datetime import datetime
import pytz


class DigiPall:
    def __init__(self, st, state, first_step,  chat_start=None,
                 bot_msg_kwargs={}, user_msg_kwargs={}, chat_len=200):

        self.st = st
        self.state = state
        self.first_step = first_step
        self.chat_start = chat_start
        self.bot_msg_kwargs = bot_msg_kwargs
        self.user_msg_kwargs = user_msg_kwargs
        self.chat_len = chat_len
        if ('chat' not in state) or (state['chat'] is None):
            self.state['chat'] = []
            self.reset()

    # function which gives utc timestamp in nanoseconds
    def get_timestamp(self):
        # get timestamp für Europe/Zurich in iso format
        return datetime.now(pytz.timezone('Europe/Zurich')).isoformat(timespec='seconds')

    def reset(self):
        self.state['step'] = self.first_step
        self.state['chat_start_time'] = self.get_timestamp()
        self.state['locked'] = False  # if locked, no new messages can be added
        self.add_msg('reset', who='app')

    def delete(self):
        self.state['chat'] = []
        self.reset()

    def run(self):
        fun = self.__class__.__dict__[self.state['step']]
        fun(self)

    def rerun(self, step):
        self.state['step'] = step
        self.st.experimental_rerun()

    def chat(self):
        for i, el in enumerate(self.state['chat']):
            if el['timestamp'] >= self.state['chat_start_time']:
                if el['who'] == 'bot':
                    message(el['msg'], is_user=False, key=f'chat{i}', **self.bot_msg_kwargs)
                elif el['who'] == 'user':
                    message(el['msg'], is_user=True, key=f'chat{i}', **self.user_msg_kwargs)

    def button_select(self, options, ncols=2):
        cols = self.st.columns(ncols)
        out = None
        for i, opt in enumerate(options):
            if cols[i%ncols].button(opt, key=f'sel{i}'):
                out = opt
        return out

    def add_msg(self, msg, who='bot', force_unlock=False, force_lock=False):
        if force_unlock:
            self.unlock()

        if (msg is not None) & ~self.state['locked']:

            new_msg = {'msg': msg, 'who': who, 'timestamp': self.get_timestamp(), 'step': self.state['step']}
            self.state['chat'].append(new_msg)

            # keep len of chat at max chat_len
            while len(self.state['chat']) > self.chat_len:
                self.state['chat'].pop(0)

        if force_lock:
            self.lock()


    def get_msg_index(self, step, who='user'):
        # loop backwards through the chat
        for ind in range(len(self.state['chat'])-1, -1, -1):
            item = self.state['chat'][ind]
            if (item['step'] == step) and (item['who'] == who):
                return ind

    def append_to_msg(self, msg_index, msg):
        self.state['chat'][msg_index]['msg'] += msg
        
    def get_msg(self, msg_index):
        return self.state['chat'][msg_index]['msg']

    def lock(self):
        self.state['locked'] = True

    def unlock(self):
        self.state['locked'] = False

    # ------------------ steps ------------------
    def step_condition_feedback(self):
        last_ind = self.get_msg_index('step_condition_feedback')
        if last_ind:
            last_msg = self.get_msg(last_ind-3)
            self.add_msg(f'Last time, {last_msg[7:].lower()}')
        else:
            self.add_msg('You seem to be here the first time - welcome to DigiPall!')

        self.add_msg(f'Today, {self.chat_start.lower()}')

        self.add_msg('Is your general health condition stable today?')

        if last_ind:
            last_msg = self.get_msg(last_ind)
            self.add_msg(f'Last time you answered: {last_msg}')
        else:
            self.add_msg('Just click below')

        self.lock()
        self.chat()

        selection = self.st.radio('', ['Yes', 'No'], key='feedback', horizontal=True)
        if self.st.button('Submit', key='submit'):
            self.add_msg(selection, who='user', force_unlock=True)
            if selection == 'Yes':
                self.rerun('step_new_symptoms_feedback')
            if selection == 'No':
                self.rerun('step_symptoms_feedback')

    def step_new_symptoms_feedback(self):
        self.add_msg('Do you experience worse/new symptoms?')
        self.lock()
        self.chat()
        selection = self.st.radio('',['Yes', 'No'], key='new_symptoms', horizontal=True)
        if self.st.button('Submit', key='submit'):
            self.add_msg(selection, who='user', force_unlock=True)
            if selection == 'Yes':
                self.rerun('step_symptoms_feedback')
            if selection == 'No':
                self.rerun('step_end')

    def step_symptoms_feedback(self):
        self.add_msg('Which of the following symptons is prelevnat/more pronounced?')
        self.lock()
        self.chat()
        selection = self.st.radio('',['Pain','Dyspnea','Nausea and/or vomiting','Fever','General weakness','Other'],
                                  key='symptoms',horizontal=True)
        if self.st.button('Submit', key='submit'):
            self.add_msg(selection, who='user', force_unlock=True)
            self.rerun('step_symptoms_intensity_feedback')

    def step_symptoms_intensity_feedback(self):
        self.add_msg('Please rate the intensity of the symptom on a scale from 1 to 10.')
        self.lock()
        self.chat()
        # intensity = self.button_select(['1','2','3','4','5','6','7','8','9','10'], ncols=5)
        intensity = self.st.slider('', 1, 10, 5, key='intensity')
        if self.st.button('Submit', key='submit'):
            self.add_msg(intensity, who='user',force_unlock=True)
            self.rerun('step_advice')

    def step_advice(self):
        symptom = self.get_msg(-3)
        symptom_dict = {
            'Pain': 'Have you tried taking your rescue pain medication yet?',
            'Dyspnea': 'Have you tried opening a windo, sitting in an upright position or doing inhalations?',
            'Nausea and/or vomiting': '<to be defined>',
            'Fever': '<to be defined>',
            'General weakness': '<to be defined>',
            'Other': '<to be defined>'
        }
        self.add_msg(symptom_dict[symptom])
        self.rerun('step_advice_feedback')

    def step_advice_feedback(self):
        self.add_msg('Has the suggestion helped?')
        self.chat()
        self.lock()
        selection = self.st.radio('',['Yes', 'No','Suggestion was not carried out'],
                               key='advice',horizontal=True)
        if self.st.button('Submit', key='submit'):
            self.add_msg(selection, who='user',force_unlock=True)
            self.rerun('step_end')


    def step_end(self):
        self.add_msg('Thank you for your feedback. Have a nice day!')
        self.lock()
        self.chat()




'''

        if self.state['step'] == 'start_chat':
            

        elif self.state['step'] == 'yes_no_feedback1':
            self.display_chat()
            # create two buttons
            if True:
                self.state['chat'].append('I am glad to hear that!')
                self.status = 'finished'
                self.rerun()
            else:
                self.state['chat'].append('I am sorry to hear that!')
                self.state['step'] = 'question2'
                self.rerun()

        elif self.state['step'] == 'question2':
'''





