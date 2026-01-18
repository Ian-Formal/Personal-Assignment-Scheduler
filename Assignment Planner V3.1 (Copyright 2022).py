import datetime
import tkinter
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry, Calendar
from tkinter.colorchooser import askcolor
from PIL import ImageTk, Image
import sqlite3
import math


class Task:
    """Stores all Tasks"""

    def __init__(self, subject, name, date, state, group, occurrence, description, task_id):
        """Initializing Subject Data Values"""
        self.subject = subject
        self.name = name
        self.date = date
        self.state = state

        self.group = group
        self.main_task = False
        if self.group != 'N/A':
            self.main_group = self.group.split('.')
            group = self.main_group.pop(-1)
            # self.main_group.pop(-1)
            self.main_group = '.'.join(self.main_group)
        else:
            self.main_group = ''
        if group == '0':
            self.main_task = True
        self.tasks = []
        self.tasks_length = 0

        self.occurrence = occurrence
        occurrences = self.occurrence.split(' ')
        if len(occurrences) < 2:
            occurrences = [-1, '', '']
        elif len(occurrences) == 2:
            occurrences.append('')
        self.occurrence_times = occurrences[0]
        self.occurrence_type = occurrences[1]
        self.occurrence_days = occurrences[2]
        self.temp_day = datetime.date(int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%Y')),
                                      int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%m')),
                                      int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%d')))

        self.description = description
        self.id = task_id
        self.reminder = ''
        self.init_reminder()

    def days_till_due(self):
        """Calculates When Things are Due"""
        self.temp_day = datetime.date(int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%Y')),
                                      int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%m')),
                                      int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%d')))
        today = datetime.date(int(datetime.datetime.now().strftime('%Y')),
                              int(datetime.datetime.now().strftime('%m')),
                              int(datetime.datetime.now().strftime('%d')))
        return (self.temp_day - today).days

    def init_reminder(self):
        """Reminder for when task is due"""
        difference = self.days_till_due()
        if 'c' in self.state:
            self.reminder = ''
        elif difference < 0:
            self.reminder = "OVERDUE!!!"
        elif difference == 0:
            self.reminder = "Due Today!"
        elif difference <= 1:
            self.reminder = "Due Tomorrow"
        elif difference <= 7:
            if not ('4' in self.state) or difference <= 2:
                time = str(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%A'))
                self.reminder = ''.join(["Due ", time])
        elif difference <= 14:
            if '1' in self.state:
                time = str(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%A'))
                self.reminder = ''.join(["Due ", time, " Next Week"])
        else:
            self.reminder = ''

    def mark_complete_or_incomplete(self):
        """Marks Tasks as complete or incomplete depending on the state"""
        if self.occurrence != '':
            self.find_next_day()
        else:
            if 'c' in self.state:
                self.state = self.state.replace('c', '')
            else:
                self.state = ''.join([self.state, 'c'])

    def find_next_day(self):
        """Changes the task date according to the occurrence"""
        day = datetime.date(int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%Y')),
                            int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%m')),
                            int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%d')))
        find_next_week = False
        if self.occurrence_days != '':
            # Setting the new task date, which is one day after the due date
            o_day_n = day.weekday()
            day += datetime.timedelta(days=1)
            day_n = day.weekday()
            if o_day_n > day_n:
                day_n = 7

            # Finding what occurring days are selected on database
            day_dict = {'M': 0, 'T': 1, 'W': 2, 't': 3, 'F': 4, 'S': 5, 's': 6}
            occurrences = []
            for row in day_dict:
                if row in self.occurrence_days:
                    occurrences.append(day_dict[row])

            # Finding out what days of the week the new task date passed
            passed_dates = []
            for row in occurrences:
                if row - day_n >= 0:
                    break
                passed_dates.append(row)

            # If the new task date is in, between or before occurring dates, then the new date will be the next
            # occurring date
            if len(passed_dates) < len(occurrences):
                new_date = occurrences[len(passed_dates)]
                new_date += 1
                if new_date > 6:
                    new_date = 0
                week = day.strftime('%W')
                date = datetime.datetime.strptime(f'{new_date}/{week}/{day.year}', '%w/%W/%Y')
                month = str(date.month).zfill(2)
                self.date = '/'.join([str(date.day), month, str(date.year)])

            # if the new task date passed all the dates, then it will calculate tne next week using commands below
            else:
                find_next_week = True
                day -= datetime.timedelta(days=occurrences[-1] - occurrences[0] + 1)
                self.temp_day = day

        # Calculates next day/week
        if self.occurrence_days == '' or find_next_week:
            self.find_next_week(day, find_next_week)

    def find_next_week(self, day, find_date_from_week):
        """Finding the next day/week the task is due"""
        if self.occurrence_type == 'D' or self.occurrence_type == 'W':
            # If daily, adds a day, if weekly, add 7 days
            type_adder = {'D': 1, 'W': 7}
            days = int(self.occurrence_times) * int(type_adder[self.occurrence_type])
        elif self.occurrence_type == 'M' or self.occurrence_type == 'Y':
            days = 0
            temp_date = day
            # If yearly, add 12 months
            if self.occurrence_type == 'Y':
                adder = int(self.occurrence_times) * 12
            else:
                adder = int(self.occurrence_times)
            for i in range(int(day.month), int(day.month) + adder):
                # adding months for each loop, calculates the number of days in that month
                adder = (temp_date.replace(month=temp_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
                # Add to the day counter
                days += adder
                # To the next month
                temp_date += datetime.timedelta(days=adder)
        else:
            days = 0
        date = day + datetime.timedelta(days=days)
        month = str(date.month).zfill(2)
        self.date = '/'.join([str(date.day), month, str(date.year)])
        if find_date_from_week:
            self.find_new_date_from_week()

    def find_new_date_from_week(self):
        """Setting the new task date when the task date is moved"""
        day = datetime.date(int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%Y')),
                            int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%m')),
                            int(datetime.datetime.strptime(self.date, '%d/%m/%Y').date().strftime('%d')))
        day_dict = {'M': 0, 'T': 1, 'W': 2, 't': 3, 'F': 4, 'S': 5, 's': 6}
        occurrences = []
        for row in day_dict:
            if row in self.occurrence_days:
                occurrences.append(day_dict[row])
        # If occurrence type != W, it will adjust the new date to the closest to prior date
        if self.occurrence_type != 'W':
            if abs(day.weekday() - occurrences[0]) > 3:
                day += datetime.timedelta(weeks=1)
        new_date = occurrences[0]
        new_date += 1
        if new_date > 6:
            new_date = 0
        week = day.strftime('%W')
        date = datetime.datetime.strptime(f'{new_date}/{week}/{day.year}', '%w/%W/%Y')
        # if new month equals to old month, add 1 week
        if date.month == self.temp_day.month and self.occurrence_type == 'M':
            date += datetime.timedelta(weeks=1)
        month = str(date.month).zfill(2)
        self.date = '/'.join([str(date.day), month, str(date.year)])

    def length(self):
        """Returns the length, this is for task view mode"""
        return self.tasks_length

    def task_progress(self):
        """Returns the progress of the main task"""
        progress = ''
        if self.tasks_length != 0:
            progress = 0
            for task in self.tasks:
                if 'c' in task.state:
                    progress += 1
            progress = f'( {progress} / {self.tasks_length} )'
        return progress


class Subject:
    """Store Subject Data From Timetable
    THIS OBJECT IS ONLY USED IN TIMETABLE"""

    def __init__(self, line, name, occurrence, items, description):
        """Initializes Subject Data"""
        self.line = line
        self.name = name
        self.occurrence = occurrence
        self.items = items.split(',')
        if '' in self.items:
            self.items.remove('')
        self.description = description
        self.tasks = []
        self.init_tasks()

    def init_tasks(self):
        """Initializes tasks list"""
        for row in assignment:
            group = assignment[row].group.split('.')
            append = False
            if group[-1] == '0' and len(group) <= 2:
                append = True
            elif group[-1] == 'N/A':
                append = True
            if assignment[row].subject == self.name and append:
                self.tasks.append(assignment[row])
        sorting_items(self)

    def add_task(self, task):
        """Adds a task into the subject"""
        self.tasks.append(task)


class State:
    """Stores task according to given State"""

    def __init__(self, state):
        """Initializes States"""
        self.tasks = []
        self.state = state
        # To Stop Errors on View Menu:
        self.main_group = 0

    def add_task(self, task):
        """Adds a task to the state list"""
        self.tasks.append(task)

    def length(self):
        state_tasks = 0
        for task in self.tasks:
            if task.group == 'N/A' or task.main_task and len(task.group.split('.')) <= 2:
                state_tasks += 1
        return state_tasks


class Timetable:
    """ALL TIMETABLE FUNCTIONS"""

    def __init__(self):
        """Initialize time now, Periods and Lines"""
        # Time Now
        time = datetime.datetime.now()
        self.hour = int(time.hour)
        self.minute = int(time.minute)
        self.day = time.strftime('%A')
        self.nxt_day = (time + datetime.timedelta(days=1)).strftime('%A')

        # Periods
        self.P1_time = "8:30"
        self.P2_time = "9:20"
        self.P3_time = "11:00"
        self.P4_time = "11:40"
        self.P5_time = "13:50"
        self.P6_time = "14:35"
        self.P7_time = "15:15"
        self.period_dict = {1: self.P1_time, 2: self.P2_time, 3: self.P3_time, 4: self.P4_time, 5: self.P5_time,
                            6: self.P6_time, 7: self.P7_time}  # Edit in Database as well

        # Lines (Subjects)
        self.line1 = str(SQL.get_line_subject_data(1)[0][1])  # FIRST THING MONDAY
        self.line2 = str(SQL.get_line_subject_data(2)[0][1])  # SECOND LESSON MONDAY
        self.line3 = str(SQL.get_line_subject_data(3)[0][1])  # AFTER HG ON MONDAY
        self.line4 = str(SQL.get_line_subject_data(4)[0][1])  # LAST LESSON ON MONDAY
        self.line5 = str(SQL.get_line_subject_data(5)[0][1])  # FIRST THING TUESDAY
        self.line6 = str(SQL.get_line_subject_data(6)[0][1])  # AFTER RECESS ON TUESDAY
        self.line7 = str(SQL.get_line_subject_data(7)[0][1])  # LAST LESSON ON TUESDAY
        self.line8 = str(SQL.get_line_subject_data(8)[0][1])  # HG
        self.line9 = str(SQL.get_line_subject_data(9)[0][1])  # Other
        self.line_dict = {1: self.line1, 2: self.line2, 3: self.line3, 4: self.line4, 5: self.line5,
                          6: self.line6, 7: self.line7, 8: self.line8, 9: self.line9}  # Edit this in Database as well

        # Init Timetable Dictionary
        self.timetable = {}

    def subject_line(self):
        """Finds out what period it is right now"""
        if self.minute < 5:
            if self.hour < 1:
                time = datetime.datetime.strptime(''.join([str(self.hour + 23), ':', str(self.minute + 55)]), '%H:%M')
            else:
                time = datetime.datetime.strptime(''.join([str(self.hour - 1), ':', str(self.minute + 55)]), '%H:%M')
        else:
            time = datetime.datetime.strptime(''.join([str(self.hour), ':', str(self.minute - 5)]), '%H:%M')
        period = 7
        for line in self.period_dict:
            if time > datetime.datetime.strptime(self.period_dict[line], '%H:%M'):
                period = line
        return period

    def Now_Subject(self):
        """Finds out the lesson you are doing right now from the subject line
        ALSO INITIALIZES TIMETABLE OBJECTS FULLY"""

        """Initialization"""
        day = {}  # Dictionary for what subjects are on a day
        row_dict = {1: 'M', 2: 'T', 3: 'W', 4: 't', 5: 'F'}  # Configuration Dictionary for Database
        for i in range(1, 6):  # Repeats for all days (Monday - Friday)
            day[i] = {}
            for j in self.period_dict:  # Repeats for all periods in a day
                # Finding what subject that occurs on day and period
                subject = SQL.get_occurrence_subject_data(f'{row_dict[i]}{j}')
                try:
                    day[i][j] = str(subject[0][1])  # Appending to timetable
                except IndexError:
                    day[i][j] = self.line9  # If fails Due to Database Failure, Subject is set to Other
        self.timetable = {1: day[1], 2: day[2], 3: day[3], 4: day[4], 5: day[5]}

        """Finds out what subject it is right now"""
        try:
            if self.day == "Monday":
                subject_now = day[1][self.subject_line()]
            elif self.day == "Tuesday":
                subject_now = day[2][self.subject_line()]
            elif self.day == "Wednesday":
                subject_now = day[3][self.subject_line()]
            elif self.day == "Thursday":
                subject_now = day[4][self.subject_line()]
            elif self.day == "Friday":
                subject_now = day[5][self.subject_line()]
            else:
                subject_now = self.line9
        except KeyError:
            subject_now = self.line9
        if subject_now == self.line9:
            pass
        return subject_now


class Events:
    """Stores all events"""

    def __init__(self, name, s_date, e_date, orig_id, occurrence, description, col, event_id):
        self.name = name
        self.s_date = s_date
        self.e_date = e_date
        self.start_date = datetime.datetime.strptime(self.s_date, '%d/%m/%Y %H:%M')
        self.end_date = datetime.datetime.strptime(self.e_date, '%d/%m/%Y %H:%M')
        self.date_diff = int((self.end_date - self.start_date).seconds / 60)
        self.orig_id = orig_id
        self.occurrence = occurrence

        occurrence = self.occurrence.split(' ')
        if len(occurrence) < 2:
            occurrence = [-1, '', '']
        elif len(occurrence) == 2:
            occurrence.append('')
        self.occurrence_times = occurrence[0]
        self.occurrence_type = occurrence[1]
        self.occurrence_days = occurrence[2]
        self.temp_day = self.start_date

        self.description = description
        self.color = col
        self.id = event_id
        self.notify = 'False'

        self.check_date_times()

    def check_date_times(self):
        date = datetime.datetime.now()
        s_date_limiter = date + datetime.timedelta(hours=24)
        if date < self.start_date < s_date_limiter:
            self.notify = 'UpComing'
        elif self.start_date < date < self.end_date:
            self.notify = 'During'
        elif self.end_date < date:
            if self.occurrence != '':
                self.tick_occurrence()
                self.check_date_times()
            else:
                self.notify = 'Past'

    def tick_occurrence(self):
        self.find_next_day()
        self.end_date = self.start_date + datetime.timedelta(minutes=self.date_diff)
        self.e_date = f'{self.end_date.day}/{self.end_date.month}/{self.end_date.year} ' \
                      f'{self.end_date.hour}:{self.end_date.minute}'

    def find_next_day(self):
        """Changes the task date according to the occurrence"""
        day = self.start_date
        find_next_week = False
        if self.occurrence_days != '':
            # Setting the new task date, which is one day after the due date
            o_day_n = day.weekday()
            day += datetime.timedelta(days=1)
            day_n = day.weekday()
            if o_day_n > day_n:
                day_n = 7

            # Finding what occurring days are selected on database
            day_dict = {'M': 0, 'T': 1, 'W': 2, 't': 3, 'F': 4, 'S': 5, 's': 6}
            occurrences = []
            for row in day_dict:
                if row in self.occurrence_days:
                    occurrences.append(day_dict[row])

            # Finding out what days of the week the new task date passed
            passed_dates = []
            for row in occurrences:
                if row - day_n >= 0:
                    break
                passed_dates.append(row)

            # If the new task date is in, between or before occurring dates, then the new date will be the next
            # occurring date
            if len(passed_dates) < len(occurrences):
                new_date = occurrences[len(passed_dates)]
                new_date += 1
                if new_date > 6:
                    new_date = 0
                week = day.strftime('%W')
                date = datetime.datetime.strptime(f'{new_date}/{week}/{day.year}', '%w/%W/%Y')
                month = str(date.month).zfill(2)
                self.s_date = '/'.join([str(date.day), month, str(date.year)])
                self.s_date = self.s_date + ' ' + str(day.hour) + ':' + str(day.minute)
                self.start_date = datetime.datetime.strptime(self.s_date, '%d/%m/%Y %H:%M')

            # if the new task date passed all the dates, then it will calculate tne next week using commands below
            else:
                find_next_week = True
                day -= datetime.timedelta(days=occurrences[-1] - occurrences[0] + 1)
                self.temp_day = day

        # Calculates next day/week
        if self.occurrence_days == '' or find_next_week:
            self.find_next_week(day, find_next_week)

    def find_next_week(self, day, find_date_from_week):
        """Finding the next day/week the task is due"""
        if self.occurrence_type == 'D' or self.occurrence_type == 'W':
            # If daily, adds a day, if weekly, add 7 days
            type_adder = {'D': 1, 'W': 7}
            days = int(self.occurrence_times) * int(type_adder[self.occurrence_type])
        elif self.occurrence_type == 'M' or self.occurrence_type == 'Y':
            days = 0
            temp_date = day
            # If yearly, add 12 months
            if self.occurrence_type == 'Y':
                adder = int(self.occurrence_times) * 12
            else:
                adder = int(self.occurrence_times)
            for i in range(int(day.month), int(day.month) + adder):
                # adding months for each loop, calculates the number of days in that month
                adder = (temp_date.replace(month=temp_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
                # Add to the day counter
                days += adder
                # To the next month
                temp_date += datetime.timedelta(days=adder)
        else:
            days = 0
        date = day + datetime.timedelta(days=days)
        month = str(date.month).zfill(2)
        self.s_date = '/'.join([str(date.day), month, str(date.year)])
        self.s_date = self.s_date + ' ' + str(day.hour) + ':' + str(day.minute)
        self.start_date = datetime.datetime.strptime(self.s_date, '%d/%m/%Y %H:%M')
        if find_date_from_week:
            self.find_new_date_from_week()

    def find_new_date_from_week(self):
        """Setting the new task date when the task date is moved"""
        day = self.start_date
        day_dict = {'M': 0, 'T': 1, 'W': 2, 't': 3, 'F': 4, 'S': 5, 's': 6}
        occurrences = []
        for row in day_dict:
            if row in self.occurrence_days:
                occurrences.append(day_dict[row])
        # If occurrence type != W, it will adjust the new date to the closest to prior date
        if self.occurrence_type != 'W':
            if abs(day.weekday() - occurrences[0]) > 3:
                day += datetime.timedelta(weeks=1)
        new_date = occurrences[0]
        new_date += 1
        if new_date > 6:
            new_date = 0
        week = day.strftime('%W')
        date = datetime.datetime.strptime(f'{new_date}/{week}/{day.year}', '%w/%W/%Y')
        # if new month equals to old month, add 1 week
        if date.month == self.temp_day.month and self.occurrence_type == 'M':
            date += datetime.timedelta(weeks=1)
        month = str(date.month).zfill(2)
        self.s_date = '/'.join([str(date.day), month, str(date.year)])
        self.s_date = self.s_date + ' ' + str(day.hour) + ':' + str(day.minute)
        self.start_date = datetime.datetime.strptime(self.s_date, '%d/%m/%Y %H:%M')


class Database:
    """Get Information, Edit Information and Import Information Back to SQLite3 Database"""

    def __init__(self):
        """Connecting to database and creates tables, if table exists, skips the table"""
        self.con = sqlite3.connect('Main.db')  # Connect to Database
        self.cur = self.con.cursor()  # Creates

        # Tasks Table
        try:
            self.cur.execute("CREATE TABLE tasks (subject TEXT, task TEXT, date TEXT, state TEXT, groups TEXT, "
                             "occurrence TEXT, description TEXT)")
        except sqlite3.OperationalError:
            pass

        # Timetable Table
        try:
            self.cur.execute("CREATE TABLE timetable (line INTEGER, subject TEXT, occurrence TEXT, items TEXT, "
                             "description TEXT)")
            self.init_subject()
        except sqlite3.OperationalError:
            pass

        # Events Table
        try:
            self.cur.execute("CREATE TABLE events (name TEXT, s_date TEXT, e_date TEXT, orig_id TEXT, "
                             "occurrence TEXT, description TEXT, col TEXT)")
        except sqlite3.OperationalError:
            pass

        # Customization Settings Table
        try:
            self.cur.execute("CREATE TABLE cus_settings (widget TEXT, font TEXT, fontsize TEXT, background_col TEXT, "
                             "background2_col TEXT, tree_row_height TEXT)")
            self.cus_settings_init()
        except sqlite3.OperationalError:
            pass

    # Task Database
    def append_task(self, subject, task, date, state, group, occurrence, description):
        """Insert task into database"""
        self.cur.execute("INSERT INTO tasks VALUES "
                         "(:subject, :task, :date, :state, :groups, :occurrence, :description)",
                         {
                             'subject': subject, 'task': task, 'date': date, 'state': state, 'groups': group,
                             'occurrence': occurrence, 'description': description
                         }
                         )
        self.con.commit()
        print("Successfully Appended Task")

    def get_task_data(self):
        """Gets all tasks from task table"""
        self.cur.execute("SELECT *, oid FROM tasks ")
        return self.cur.fetchall()

    def get_specific_task_data(self, heading, specifier):
        """Gets all tasks from task table that fits a heading and a specifier"""
        # self.cur.execute("SELECT *, oid FROM tasks WHERE :heading=:specifier",
        #                  {'heading': heading, 'specifier': specifier})
        # return self.cur.fetchall()
        task = self.get_task_data()
        all_tasks = []
        for row in task:
            if row[heading] == specifier:
                all_tasks.append(row)
        return all_tasks

    def modify_task(self, task, task_id: int):
        """Modifies a task without modifying its group"""
        self.cur.execute("UPDATE tasks SET subject = :subject, task = :task, date = :date"
                         ", state = :state, groups = :groups, occurrence = :occurrence, description = :description "
                         "WHERE ROWID = :id",
                         {'subject': task.subject, 'task': task.name, 'date': task.date,
                          'state': task.state, 'groups': task.group, 'occurrence': task.occurrence,
                          'description': task.description, 'id': task_id})
        self.con.commit()

    def modify_task_state(self, task, task_id: int):
        """Modifies a task state"""
        self.cur.execute("UPDATE tasks SET state = :state WHERE ROWID = :id",
                         {'state': task.state, 'id': task_id})
        self.con.commit()

    def modify_task_group(self, group, task_id: int):
        """Modifies a task group"""
        self.cur.execute("UPDATE tasks SET groups = :groups WHERE ROWID = :id",
                         {'groups': group, 'id': task_id})
        self.con.commit()

    def modify_task_groups(self, task_del):
        """Modifies task groups from deleting one line"""
        if task_del.group == 'N/A':
            self.delete_task(task_del.id)
        elif task_del.main_task:
            self.delete_tasks_with_group(task_del.main_group)
        else:
            row_id = task_del.group.split('.')
            row_id = row_id[-1]
            main_task = self.get_specific_task_data(4, '.'.join([task_del.main_group, '0']))
            all_tasks = assignment[main_task[0][-1]].tasks
            all_tasks = sorting_groups(all_tasks)
            for task in range(int(row_id), len(all_tasks)):
                group = all_tasks[task].group.split('.')
                group[-1] = str(int(group[-1]) - 1)
                group = '.'.join(group)
                self.modify_task_group(group, all_tasks[task].id)
            self.delete_task(task_del.id)

    def modify_task_occurrence(self, occurrence, task_id: int):
        """Modifies a task occurrence"""
        self.cur.execute("UPDATE tasks SET occurrence = :occurrence WHERE ROWID = :id",
                         {'occurrence': occurrence, 'id': task_id})
        self.con.commit()

    def modify_task_description(self, description, task_id: int):
        """Modifies a task description"""
        self.cur.execute("UPDATE tasks SET description = :description WHERE ROWID = :id",
                         {'description': description, 'id': task_id})
        self.con.commit()

    def delete_tasks_with_group(self, group):
        """Deletes task groups"""
        self.cur.execute("DELETE from tasks WHERE groups LIKE '{0}'".format(group + '%'))
        self.con.commit()

    def delete_task(self, task_id: int):
        """Delete Task"""
        self.cur.execute("DELETE from tasks WHERE ROWID = :id", {'id': task_id})
        self.con.commit()

    # TIMETABLE DATABASE
    def init_subject(self):
        """Initializing Timetable Table if created"""
        global SQL
        SQL = Database()
        line_dict = range(1, 10)
        for i in range(1, len(line_dict) + 1):  # Creating Lines
            self.cur.execute("INSERT INTO timetable VALUES (:line, :subject, :occurrence, :items, :description)",
                             {'line': i, 'subject': 'Other', 'occurrence': '', 'items': '', 'description': ''})
            self.con.commit()

        # Creating Occurrences (All occurrences will be on line1)
        occurrence_dict = {1: 'M', 2: 'T', 3: 'W', 4: 't', 5: 'F'}
        period_dict = range(1, 8)
        for x in range(1, len(occurrence_dict) + 1):
            day = occurrence_dict[x]
            for y in range(1, len(period_dict) + 1):
                data = self.get_line_subject_data(1)[0][2]
                occurrence = ''.join([data, ' ', day + str(y)])
                self.modify_occurrence(1, occurrence)

    def get_all_subject_data(self):
        """Gets all subject data from timetable table"""
        self.cur.execute("SELECT *, oid FROM timetable ")
        return self.cur.fetchall()

    def get_line_subject_data(self, line: int):
        """Gets all subject data from timetable table which line = line"""
        self.cur.execute("SELECT *, oid FROM timetable WHERE line=:line", {'line': line})
        return self.cur.fetchall()

    def get_occurrence_subject_data(self, occurrence):
        """Gets all subject data from timetable table which occurrence has occurrence"""
        # self.cur.execute("SELECT *, oid FROM timetable WHERE occurrence LIKE '%{0}%'".format(occurrence))
        data = self.get_all_subject_data()
        result = []
        for row in data:
            if occurrence in row[2]:
                result.append(row)
        return result

    def modify_subject(self, line: int, new_subject):
        """Modify a subject"""
        self.cur.execute("UPDATE timetable SET subject=:subject WHERE line=:line", {'subject': new_subject,
                                                                                    'line': line})
        self.con.commit()

    def modify_occurrence(self, line: int, occurrence):
        """Modify an occurrence"""
        self.cur.execute("UPDATE timetable SET occurrence=:occurrence WHERE line=:line", {'occurrence': occurrence,
                                                                                          'line': line})
        self.con.commit()

    def modify_subject_details(self, line: int, items, description):
        """Modifies subject description and items"""
        self.cur.execute("UPDATE timetable SET items=:items, description=:description WHERE line=:line",
                         {'items': items, 'description': description, 'line': line})
        self.con.commit()

    # Events Database
    def append_event(self, name, s_date: str, e_date: str, orig_id: str, occurrence, description, col):
        self.cur.execute("INSERT INTO events VALUES (:name, :s_date, :e_date, :orig_id, :occurrence, "
                         ":description, :col)", {
                             'name': name, 's_date': s_date, 'e_date': e_date, 'orig_id': orig_id,
                             'occurrence': occurrence, 'description': description, 'col': col
                         })
        self.con.commit()

    def get_all_events(self):
        self.cur.execute("SELECT *, oid FROM events")
        return self.cur.fetchall()

    def get_events_in_date(self, date):
        all_event = self.get_all_events()
        date = datetime.datetime.strptime(date, '%d/%m/%Y')
        all_events = []
        for event in all_event:
            s_date = datetime.datetime.strptime(event[1], '%d/%m/%Y %H:%M')
            e_date = datetime.datetime.strptime(event[2], '%d/%m/%Y %H:%M')
            if s_date.date() <= date.date() <= e_date.date():
                all_events.append(event)
        return all_events

    def get_events_with_oid(self, orig_id):
        self.cur.execute("SELECT *, oid FROM events WHERE orig_id=:orig_id", {'orig_id': orig_id})
        return self.cur.fetchall()

    def modify_event(self, event, event_id: int):
        self.cur.execute("UPDATE events SET name = :name, s_date = :s_date, e_date = :e_date, "
                         "occurrence = :occurrence, description = :description, col = :col WHERE ROWID = :id", {
                             'name': event.name, 's_date': event.s_date, 'e_date': event.e_date,
                             'occurrence': event.occurrence, 'description': event.description, 'col': event.color,
                             'id': event_id
                         })
        self.con.commit()

    def delete_event(self, event_id: int):
        self.cur.execute("DELETE from events WHERE ROWID = :id", {'id': event_id})
        self.con.commit()

    # Customize Settings Database
    def cus_settings_init(self):
        """Initializes Customization Settings Database"""
        bg_color = '#e0dcd4'
        widgets = {0: ('theme', 'clam', '', '', '', ''),
                   1: ('Heading', 'Helvetica', '16', '#F7f2d1', '#F6fdff', ''),
                   2: ('Sub_Heading', 'Helvetica', '16', bg_color, '', ''),
                   3: ('Main_Button', 'Helvetica', '14', bg_color, '', ''),
                   4: ('Text', 'Helvetica', '12', bg_color, '', ''),
                   5: ('Timetable', 'Helvetica', '12', bg_color, '', ''),
                   6: ('Schedule', 'Helvetica', '9', bg_color, '', ''),
                   7: ('Frame', '', '', bg_color, '', ''),
                   8: ('Treeview', 'Helvetica', '12', bg_color, '#Ffe6cb', '28'),
                   9: ('Now_Date', 'Helvetica', '8', '#1b52f9', '', '')
                   }
        for widget in widgets:
            self.cur.execute("INSERT INTO cus_settings VALUES (:widget, :font, :fontsize, :background_col, "
                             ":background2_col, :tree_row_height)", {
                                 'widget': widgets[widget][0], 'font': widgets[widget][1],
                                 'fontsize': widgets[widget][2],
                                 'background_col': widgets[widget][3], 'background2_col': widgets[widget][4],
                                 'tree_row_height': widgets[widget][5]
                             })
        self.con.commit()

    def reset_cus_setting_values(self):
        self.cur.execute("DELETE from cus_settings")
        self.con.commit()
        self.cus_settings_init()

    def get_cus_setting_values_for(self, widget):
        self.cur.execute("SELECT *, oid FROM cus_settings WHERE widget=:widget", {'widget': widget})
        return self.cur.fetchall()

    def modify_cus_setting_values_for(self, widget, font, fontsize, background, background2, tree_row_height):
        self.cur.execute("UPDATE cus_settings SET font = :font, fontsize = :fontsize, background_col = :background_col,"
                         " background2_col = :background2_col, tree_row_height = :tree_row_height "
                         "WHERE widget = :widget", {'widget': widget, 'font': font, 'fontsize': fontsize,
                                                    'background_col': background, 'background2_col': background2,
                                                    'tree_row_height': tree_row_height})
        self.con.commit()

    def close(self):
        """Closes Database"""
        self.con.commit()  # Committing Changes
        self.con.close()  # Closes Connection


subject_sort = {}


def sorting_items(category):
    """Sorts out items in different categories(state)"""
    global subject_sort, Now
    category_list = []
    for row in category.tasks:
        category_list.append([row.subject, row.name, row.date, row.state, row.group, row.id])
    Now = Timetable()
    Now.Now_Subject()
    subject_sort = {Now.line1: 1, Now.line2: 2, Now.line3: 3, Now.line4: 4,
                    Now.line5: 5, Now.line6: 6, Now.line7: 7, Now.line8: 8, Now.line9: 9}
    # Subject Sort is Custom Sort for Subjects
    new_list = category_list
    try:
        new_list = sorted(sorted(sorted(sorted(category_list,
                                               key=lambda x: x[1]),
                                        key=lambda x: datetime.datetime.strptime(x[2], "%d/%m/%Y")),
                                 key=lambda x: subject_sort[x[0]]),
                          key=lambda x: x[3])
    except ValueError:
        print("SERIOUS ISSUE FOUND: SORTING_ITEMS FUNCTION DETECTED. PLEASE CHECK DATABASE TO SEE "
              "IF THERE ARE ANY PROBLEMS LIKE DATES AND SUBJECTS")
    category.tasks = []
    for row in new_list:
        category.add_task(assignment[row[-1]])


def sorting_groups(tasks_list):
    """Sort Sub Tasks Order"""
    new_list = []
    for row in tasks_list:
        new_list.append([row.group, row.id])
    new_list = sorted(new_list, key=lambda x: x[0])
    result_list = []
    for row in new_list:
        result_list.append(assignment[row[1]])
    return result_list


def sort_data():
    """Sorts data into different state objects"""
    Important.tasks = []
    Quick_Task.tasks = []
    _Task_.tasks = []
    Casual_Task.tasks = []
    Completed.tasks = []
    for task in assignment:
        if assignment[task].state == '1':
            Important.add_task(assignment[task])
        elif assignment[task].state == '2':
            Quick_Task.add_task(assignment[task])
        elif assignment[task].state == '3':
            _Task_.add_task(assignment[task])
        elif assignment[task].state == '4':
            Casual_Task.add_task(assignment[task])
        elif 'c' in assignment[task].state:
            Completed.add_task(assignment[task])
    sorting_items(Important)
    sorting_items(Quick_Task)
    sorting_items(_Task_)
    sorting_items(Casual_Task)
    sorting_items(Completed)


def check_for_shortcuts(task_str: str):
    """Checks for shortcuts under user's input"""
    shortcuts = [[" /a", " Assignment"], [" /h", " Homework"], [" /c", " Composition"],
                 [" /t", " Task"], [" /e", " Essay"], [" /r", " Report"], [" /x", " Text"]]
    checked = task_str
    for shortcut in shortcuts:
        checked = checked.replace(str(shortcut[0]), str(shortcut[1]))
    return checked


def lighter_col(color: str, lighter_by: float | int):
    """entering 0 will return complementary and 1 will return white or black"""
    if color[0] == '#':
        lighter_by = float(lighter_by)
        color = color.lstrip('#')
        rgb = list(int(color[i:i + 2], 16) for i in (0, 2, 4))
        for number, color_value in enumerate(rgb):
            if lighter_by == 0:
                rgb[number] = int(255 - color_value)
            elif lighter_by != 1:
                rgb[number] = int(math.ceil(color_value * lighter_by))
                if rgb[number] > 255:
                    rgb[number] = 255
        if lighter_by == 1:
            combined = sum(rgb) > 383
            if combined:
                return '#000000'
            else:
                return '#ffffff'
        rgb = tuple(rgb)
        return '#%02x%02x%02x' % rgb
    else:
        return '#ffffff'


def find_middle_col(colors: list):
    if colors[0][0] == '#' and colors[1][0] == '#':
        color1 = colors[0].lstrip('#')
        rgb1 = list(int(color1[i:i + 2], 16) for i in (0, 2, 4))
        color2 = colors[1].lstrip('#')
        rgb2 = list(int(color2[i:i + 2], 16) for i in (0, 2, 4))
        rgb = (int(math.ceil((rgb1[0] + rgb2[0]) / 2)), int(math.ceil((rgb1[1] + rgb2[1]) / 2)),
               int(math.ceil((rgb1[2] + rgb2[2]) / 2)))
        return '#%02x%02x%02x' % rgb
    else:
        return '#000000'


class Tkinter:
    """Tkinter Main Elements (Mainloop)"""

    def __init__(self, master):
        """Initializes Tkinter window"""
        self.root = master
        self.root.geometry("+150+70")
        master.title("Assignment Planner V3.1 (Copyright 2022, Ian Au)")
        master.iconbitmap("Images/icon.ico")
        self.style = ttk.Style(master)
        self.img1 = ImageTk.PhotoImage(Image.open("Images/background1.jpg"))
        self.background()

        # Initialize Menu tabs
        self.nb = ttk.Notebook(self.root, style='TNotebook')
        self.page1 = ttk.Frame(self.nb, style='main.TFrame')
        self.page2 = ttk.Frame(self.nb, style='main.TFrame')
        self.page3 = ttk.Frame(self.nb, style='main.TFrame')
        self.page4 = ttk.Frame(self.nb, style='main.TFrame')
        self.pg1 = None
        self.pg2 = None
        self.pg3 = None
        self.pg4 = None

        self.root.bind('<Escape>', lambda e: self.root.destroy())

    def update_init(self):
        global menu
        self.Menu_Bar()
        self.Styles()
        menu.notification_window()
        self.update_notifications()

    def Styles(self):
        """Setups Tkinter window styles"""
        global SQL
        self.style.theme_use(SQL.get_cus_setting_values_for('theme')[0][1])
        bg_col = SQL.get_cus_setting_values_for('Frame')[0][3]

        heading = SQL.get_cus_setting_values_for('Heading')[0]
        self.style.configure('TNotebook', background=heading[4])
        self.style.configure('TNotebook.Tab', font=(heading[1], int(heading[2])), padding=10,
                             foreground=lighter_col(heading[3], 1), background=heading[3])
        if lighter_col(heading[3], 1) == '#ffffff':
            self.style.map("TNotebook.Tab", background=[("selected", lighter_col(heading[3], 1.4))])
        else:
            self.style.map("TNotebook.Tab", background=[("selected", lighter_col(heading[3], 0.9))])

        sub_heading = SQL.get_cus_setting_values_for('Sub_Heading')[0]
        self.style.configure('sub_heading.TLabel', font=(sub_heading[1], int(sub_heading[2])),
                             foreground=lighter_col(bg_col, 1), background=bg_col)
        main_button = SQL.get_cus_setting_values_for('Main_Button')[0]
        self.style.configure("main.TButton", font=(main_button[1], int(main_button[2])), padding=1, relief='raised',
                             foreground=lighter_col(bg_col, 1))
        self.style.configure('main.TFrame', background=bg_col)

        text = SQL.get_cus_setting_values_for('Text')[0]
        self.style.configure('text.TLabel', font=(text[1], int(text[2])), foreground=lighter_col(bg_col, 1),
                             background=bg_col)
        timetable = SQL.get_cus_setting_values_for('Timetable')[0]
        self.style.configure('Timetable.TLabel', font=(timetable[1], int(timetable[2])),
                             foreground=lighter_col(bg_col, 1), background=bg_col)
        self.style.configure('Timetable_side.TLabel', font=(timetable[1], abs(int(timetable[2]) - 2)),
                             foreground=lighter_col(bg_col, 1), background=bg_col)
        schedule = SQL.get_cus_setting_values_for('Schedule')[0]
        self.style.configure('Schedule.TLabel', font=(schedule[1], int(schedule[2])), foreground=lighter_col(bg_col, 1),
                             background=bg_col)
        treeview = SQL.get_cus_setting_values_for('Treeview')[0]
        self.style.configure('Treeview', font=(treeview[1], treeview[2]), background=treeview[4], rowheight=treeview[5],
                             fieldbackground=treeview[4], foreground=lighter_col(treeview[4], 1))
        self.style.configure('Treeview.Heading', font=(treeview[1], abs(int(treeview[2]) - 2)), background=bg_col,
                             foreground=lighter_col(bg_col, 1))
        if lighter_col(treeview[4], 1) == '#ffffff':
            self.style.map("Treeview", background=[("selected", lighter_col(treeview[4], 1.4))])
        else:
            self.style.map("Treeview", background=[("selected", lighter_col(treeview[4], 0.9))],
                           foreground=[('selected', lighter_col(treeview[4], 1))])
        calendar_selector = SQL.get_cus_setting_values_for('Now_Date')[0][3]

        self.style.configure('TRadiobutton', font=(text[1], text[2]), foreground=lighter_col(bg_col, 1),
                             background=bg_col)
        if lighter_col(bg_col, 1) == '#ffffff':
            self.style.configure('TScrollbar', background=bg_col, bordercolor=lighter_col(bg_col, 1.4),
                                 arrowcolor=lighter_col(bg_col, 1))
        else:
            self.style.configure('TScrollbar', background=bg_col, bordercolor=lighter_col(bg_col, 0.7),
                                 arrowcolor=lighter_col(bg_col, 1))

        self.style.configure('now_date.TLabel', font=(schedule[1], schedule[2]), foreground=calendar_selector,
                             background=bg_col)
        self.style.configure('error.TLabel', font=(schedule[1], schedule[2]),
                             foreground=find_middle_col([lighter_col(bg_col, 1), '#Ff0000']), background=bg_col)
        self.style.configure('Timetable.TButton', font=(timetable[1], timetable[2]), foreground=lighter_col(bg_col, 1))
        self.style.configure('list.TButton', font=(text[1], abs(int(text[2]) - 2)), padding=5, width=28, anchor='w',
                             foreground=lighter_col(bg_col, 1))
        self.style.configure('menu.TButton', font=(main_button[1], main_button[2]), padding=1, relief='flat',
                             foreground=lighter_col(bg_col, 1))
        self.style.configure('date.TButton', font=(schedule[1], int(schedule[2]) + 2), padding=1, height=2,
                             relief='flat',
                             anchor='w', foreground=lighter_col(bg_col, 1))
        self.style.configure('now_date.TButton', font=(schedule[1], int(schedule[2]) + 2), padding=1, height=2,
                             foreground=calendar_selector, relief='flat', anchor='w')
        self.style.configure('dim_date.TButton', font=(schedule[1], int(schedule[2]) + 2), padding=1, height=2,
                             foreground='gray', relief='flat', anchor='w')
        self.style.configure('TEntry', font=(text[1], text[2]), padding=5)
        self.style.configure('TMenubutton', font=(text[1], text[2]), padding=5, foreground=lighter_col(bg_col, 1),
                             background=bg_col, arrowcolor=lighter_col(bg_col, 1))
        self.style.configure('TOptionMenu', font=(text[1], text[2]), padding=1, foreground=lighter_col(bg_col, 1))
        self.style.configure('main.TLabelframe', background=bg_col)
        self.style.configure('main.TLabelframe.Label', font=(sub_heading[1], math.ceil(int(sub_heading[2]) / 1.6)),
                             background=bg_col, foreground=lighter_col(bg_col, 1))
        self.style.configure('TCheckbutton', font=(text[1], int(text[2]) - 1), background=bg_col,
                             foreground=lighter_col(bg_col, 1))

        for widget in ('TNotebook.Tab', 'TMenubutton', 'TOptionMenu', 'dim_date.TButton', 'now_date.TButton',
                       'date.TButton', 'menu.TButton', 'list.TButton', 'Timetable.TButton', 'TRadioButton',
                       'main.TButton', 'Treeview.Heading', 'TScrollbar', 'TCheckbutton', 'TRadiobutton'):
            if widget == 'TNotebook.Tab':
                bg_col = heading[3]
            else:
                bg_col = SQL.get_cus_setting_values_for('Frame')[0][3]
            if lighter_col(bg_col, 1) == '#ffffff':
                self.style.map(widget, background=[('active', lighter_col(bg_col, 1.4)), ('!disabled', bg_col),
                                                   ('disabled', lighter_col(bg_col, 0.9))], foreground=[])
            else:
                self.style.map(widget, background=[('active', lighter_col(bg_col, 0.9)), ('!disabled', bg_col),
                                                   ('disabled', lighter_col(bg_col, 0.9))], foreground=[])

        colors = set()
        for event in event_:
            colors.add(event_[event].color)
        for color in colors:
            self.style.configure(f'{color}.TFrame', background=f'{color}')
            self.style.configure(f'{color}.TButton', foreground=f'{lighter_col(color, 1)}', background=bg_col,
                                 font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
            self.style.map(f'{color}.TButton', background=[('!active', f'{color}'),
                                                           ('active', lighter_col(color, 1.1))])
            self.style.configure(f'{color}.TLabel', foreground=f'{color}', background=bg_col, font=('Helvetica', 8))

    def Root_Title(self):
        """Root title (not used)"""
        Root_Title1 = tk.Label(self.root, text="WELCOME TO ASSIGNMENT MANAGER, HOW MAY I HELP YOU?", foreground="Blue")
        Root_Title1.grid(row=0, column=6)
        Img = tk.Label(image=self.img1)
        Img.pack()

    def Menu_Bar(self):
        """Setup Menu Options"""
        self.nb.pack()
        self.nb.add(self.page1, text='Tasks')
        self.nb.add(self.page2, text='Timetable')
        self.nb.add(self.page3, text='Planner')
        self.nb.add(self.page4, text='Settings')

        """RUNS ALL PAGES"""
        self.pg1 = Tk_Pg1(self.root, self.page1)
        self.pg2 = Tk_Pg2(self.root, self.page2)
        self.pg3 = Tk_Pg3(self.root, self.page3)
        self.pg4 = Tk_Pg4(self.root, self.page4)
        self.root.bind('1', lambda e: self.quick_navigation(0))
        self.root.bind('2', lambda e: self.quick_navigation(1))
        self.root.bind('3', lambda e: self.quick_navigation(2))
        self.root.bind('4', lambda e: self.quick_navigation(3))

    def quick_navigation(self, tab_selected):
        """Define Keyboard Shortcuts for quick navigation across tabs/pages"""
        global menu
        if not menu.tabs > 0:
            list_of_pages = [0, 1, 2, 3]
            del list_of_pages[tab_selected]
            self.disable_notebook(list_of_pages)
            self.enable_notebook()

    def get_disable_notebook_tabs(self):
        """Returns all notebook pages except the current page selected and the current page selected"""
        list_of_pages = [0, 1, 2, 3]
        current_page = self.nb.index(self.nb.select())
        del list_of_pages[current_page]
        return list_of_pages, current_page

    def background(self):
        """Background Image"""
        tk.Label(self.root, image=self.img1).place(x=0, y=0, relheight=1, relwidth=1)

    def update_notifications(self):
        """Ticks Notifications to check for updates to show notification menu"""
        global menu
        for event in event_:
            original_note = event_[event].notify
            event_[event].check_date_times()
            if original_note != event_[event].notify:
                menu.notification_window()

        self.root.after((60 - datetime.datetime.now().second) * 1000 +
                        int(1000 - round(datetime.datetime.now().microsecond / 1000)),
                        lambda: self.update_notifications())

    def disable_notebook(self, tab):
        """Disables Notebook"""
        for i in tab:
            self.nb.tab(i, state='disabled')

    def enable_notebook(self):
        """Enables Notebook"""
        self.nb.tab(0, state='normal')
        self.nb.tab(1, state='normal')
        self.nb.tab(2, state='normal')
        self.nb.tab(3, state='normal')


class Tk_Pg1:
    """Functions and setup for Page1, View Mode"""

    def __init__(self, master, pg_master):
        """Initializes Page 1"""
        self.root = master
        pg_master.rowconfigure(0, weight=1)
        pg_master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(window.page1, relief='raised', padding=10, style='main.TFrame')
        self.frame.grid(row=0, column=0, sticky='NSEW')

        self.tree_frame = ttk.Frame(self.frame, relief='flat', width=750, style='main.TFrame')
        self.tree_frame.grid(row=0, column=0, columnspan=2, sticky='NSEW', pady=5)
        self.x_scroll = ttk.Scrollbar(self.tree_frame, orient='horizontal')
        self.y_scroll = ttk.Scrollbar(self.tree_frame, orient='vertical')
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.y_scroll.set, xscrollcommand=self.x_scroll.set,
                                 selectmode='browse')
        self.y_scroll.config(command=self.tree.yview)
        self.x_scroll.config(command=self.tree.xview)
        self.iid = ''

        self.n_button = ttk.Button(self.frame, text='Write New Task', command=self.write_task_menu,
                                   style='main.TButton')
        self.n_button.grid(row=1, column=0, padx=10, pady=25, sticky='e')
        self.m_button = ttk.Button(self.frame, text='Show Task Menu For Task Selected', command=self.view_task_menu,
                                   style='main.TButton')
        self.m_button.grid(row=1, column=1, padx=10, pady=25, sticky='w')
        self.c_button = ttk.Button(self.frame, text='Mark Selected Task As Completed/Incomplete',
                                   command=self.mark_task_complete_or_incomplete, style='main.TButton')
        self.c_button.grid(row=2, column=0, columnspan=2, padx=5, pady=1)

        self.treeview_init()
        self.tasks_init()
        self.root.bind('<Control-Key-t>', lambda e: self.write_task_menu())

    def treeview_init(self):
        """Initialize all treeview columns and length"""
        # Define Columns
        self.tree['columns'] = ('Task', 'Due Date', 'Category', 'Reminders')

        # Format Columns
        self.tree.column('#0', width=200, minwidth=190, stretch=True)
        self.tree.column('Task', anchor='w', width=300, minwidth=200, stretch=True)
        self.tree.column('Due Date', anchor='w', width=100, minwidth=25, stretch=True)
        self.tree.column('Category', anchor='w', width=100, minwidth=90, stretch=True)
        self.tree.column('Reminders', anchor='w', width=150, minwidth=100, stretch=True)

        # Headings
        self.tree.heading('#0', text='Category/Subject', anchor='w')
        self.tree.heading('Task', text='Task Name', anchor='w')
        self.tree.heading('Due Date', text='Due Date', anchor='w')
        self.tree.heading('Category', text='Category', anchor='w')
        self.tree.heading('Reminders', text='Reminders', anchor='w')

        # Show Scrollbar
        self.x_scroll.pack(side='bottom', fill='x')
        self.y_scroll.pack(side='right', fill='y')

        # Show Treeview
        self.tree.pack()
        self.tree.bind('<Double-Button-1>', lambda e: self.view_task_menu())
        self.tree.bind('<Control-1>', lambda e: self.mark_task_complete_or_incomplete())

    def tasks_init(self):
        """Writes Tasks Into Treeview"""
        sort_data()

        # State Categories
        self.tree.insert(parent='', index='end', iid='I', text='Important:\t\t' + str(Important.length()),
                         values=('', '', '', ''))
        self.tree.insert(parent='', index='end', iid='QT', text='Quick Tasks:\t' + str(Quick_Task.length()),
                         values=('', '', '', ''))
        self.tree.insert(parent='', index='end', iid='T', text='Tasks:\t\t' + str(_Task_.length()),
                         values=('', '', '', ''))
        self.tree.insert(parent='', index='end', iid='CT', text='Casual Tasks:\t' + str(Casual_Task.length()),
                         values=('', '', '', ''))
        self.tree.insert(parent='', index='end', iid='C', text='Completed:\t' + str(Completed.length()),
                         values=('', '', '', ''))

        # Show Tasks Under Categories
        self.view_category(Important, 'I')
        self.view_category(Quick_Task, 'QT')
        self.view_category(_Task_, 'T')
        self.view_category(Casual_Task, 'CT')
        self.view_category(Completed, 'C')
        for task in assignment:
            if assignment[task].main_task and not assignment[task].length() == 0:
                assignment[task].tasks = sorting_groups(assignment[task].tasks)
                self.view_category(assignment[task], str(assignment[task].id))

    def view_category(self, category, parent):
        """Writes all tasks from category onto canvas (Initialization)"""
        if category.length() == 0:
            self.iid = all_state_list[str(category.state)]
            try:
                self.tree.insert(parent=parent, index='end', iid=str(self.iid), text='None',
                                 values=('', '', '', ''))
            except tkinter.TclError:
                self.tree.insert(parent=parent, index='end', iid=str(self.iid) + category.group, text='None',
                                 values=('', '', '', ''))
        index = 0
        for row in range(0, len(category.tasks)):
            self.iid = category.tasks[row].id
            state = all_state_list[category.tasks[row].state]
            try:
                self.tree.insert(parent=parent, index=index, iid=str(self.iid), text=category.tasks[row].subject,
                                 values=(category.tasks[row].name, category.tasks[row].date,
                                         state, category.tasks[row].reminder))
            except tkinter.TclError:
                order = category.tasks[row].group.split('.')
                self.tree.delete(self.iid)
                self.tree.insert(parent=parent, index=int(order[-1]), iid=str(self.iid),
                                 text=category.tasks[row].subject, values=(category.tasks[row].name,
                                                                           category.tasks[row].date, state,
                                                                           category.tasks[row].reminder))
                if index < 1:
                    progress = category.main_group
                    progress = SQL.get_specific_task_data(4, '.'.join([progress, '0']))
                    progress = assignment[progress[0][-1]].task_progress()
                    main_task = self.tree.item(parent)
                    main_task = main_task['values']
                    self.tree.item(parent, values=(main_task[0] + '   ' + progress, main_task[1],
                                                   main_task[2], main_task[3]))
            index += 1

    def write_task_menu(self):
        """Shows write new task menu"""
        global menu
        if not menu.tabs > 0:
            menu.new_task_window()

    def view_task_menu(self):
        """Shows task menu for task selected"""
        global menu
        if not menu.tabs > 0:
            try:
                task_id = int(self.tree.selection()[0])
                menu.task_window(task_id)
            except ValueError:
                pass
            except IndexError:
                pass

    def mark_task_complete_or_incomplete(self):
        """Marks selected task as complete or incomplete"""
        global menu
        if not menu.tabs > 0:
            try:
                task_id = int(self.tree.selection()[0])
                assignment[task_id].mark_complete_or_incomplete()
                SQL.modify_task(assignment[task_id], task_id)
                self.update_treeview()
            except ValueError:
                pass
            except IndexError:
                pass

    def disable_buttons(self):
        """Disables buttons to prevent multiple menu tabs"""
        self.n_button['state'] = 'disabled'
        self.m_button['state'] = 'disabled'
        self.c_button['state'] = 'disabled'

    def update_treeview(self):
        """Updates Treeview for new or modified assignments"""
        for category in self.tree.get_children():
            self.tree.delete(category)
        tasks_initialization()
        self.tasks_init()

    def enable_buttons(self):
        """Enables buttons from their disabled state"""
        self.n_button['state'] = 'normal'
        self.m_button['state'] = 'normal'
        self.c_button['state'] = 'normal'


class Tk_Pg2:
    """Functions for Page 2: Timetable"""

    def __init__(self, master, pg_master):
        """Initializes Page 2"""
        self.root = master
        pg_master.rowconfigure(0, weight=1)
        pg_master.columnconfigure(0, weight=1)
        self.frame = ttk.Frame(window.page2, relief='raised', padding=10, style='main.TFrame')
        self.frame.grid(row=0, column=0, sticky='NSEW')
        self.frame.columnconfigure(0, weight=1)

        self.timetable_frame = ttk.Frame(self.frame, relief='raised', padding=2, style='main.TFrame')
        self.timetable_frame.grid(row=0, column=0, sticky='news')
        for i in range(0, 6):
            self.timetable_frame.columnconfigure(i, weight=1)
        self.subject_clicked = ''
        self.button_n = {}
        self.i_label = None

        self.days = range(1, 5 + 1)
        self.periods = range(1, len(Now.period_dict))

        self.view_TimeTable()
        self.view_item_list()

    def view_TimeTable(self):
        """Writes all widgets onto canvas (Initialization)"""
        # TITLE
        frame_t = ttk.Frame(self.timetable_frame, relief='solid', style='main.TFrame')
        frame_t.grid(row=0, column=0, sticky='news')
        ttk.Label(frame_t, text='TIMETABLE', style='Timetable.TLabel').grid(row=0, column=0, padx=3, pady=4)

        # X TITLE FRAMES AND LABELS
        table_x_title = {}
        day_dict = {1: 'MONDAY', 2: 'TUESDAY', 3: 'WEDNESDAY', 4: 'THURSDAY', 5: 'FRIDAY'}
        for day in self.days:
            table_x_title[day] = ttk.Frame(self.timetable_frame, relief='solid', style='main.TFrame')
            table_x_title[day].grid(row=0, column=day, sticky='news')
            ttk.Label(table_x_title[day], text='{: ^11}'.format(day_dict[day]), style='Timetable.TLabel') \
                .grid(row=0, column=0, padx=3, pady=4)

        # TIME FRAMES AND LABELS
        table_y_title = {}
        for period in self.periods:
            table_y_title[period] = ttk.Frame(self.timetable_frame, relief='groove', style='main.TFrame')
            table_y_title[period].grid(row=period, column=0, sticky='news')
            ttk.Label(table_y_title[period], text='{: ^9}\n{: >6}\n{: ^9}'
                      .format(Now.period_dict[period], '-', Now.period_dict[period + 1]),
                      style='Timetable_side.TLabel').grid(row=0, column=0, padx=30, pady=4)

        # SUBJECTS
        Now.Now_Subject()
        table_contents = {}
        for day in self.days:
            table_contents[day] = {}
            self.button_n[day] = {}
            for period in self.periods:
                table_contents[day][period] = ttk.Frame(self.timetable_frame, relief='groove', style='main.TFrame')
                table_contents[day][period].grid(row=period, column=day, sticky='news')
                self.button_n[day][period] = ttk.Button(table_contents[day][period],
                                                        text=f'{Now.timetable[day][period]}', style='Timetable.TButton',
                                                        command=lambda x=day, y=period: self.show_subject_menu(x, y))
                self.button_n[day][period].pack(expand=1, anchor='n', fill='x')

    def view_item_list(self):
        """Views what items to bring for tomorrow"""
        days_dict = {'Monday': 'M', 'Tuesday': 'T', 'Wednesday': 'W', 'Thursday': 't', 'Friday': 'F',
                     'Saturday': 'S', 'Sunday': 's'}
        subject_data = SQL.get_occurrence_subject_data(days_dict[Now.nxt_day])
        subjects = []
        for row in subject_data:
            subjects.append(Subject(row[0], row[1], row[2], row[3], row[4]))
        items = set()
        for row in subjects:
            for i in row.items:
                items.add(i.capitalize())
        if items == set():
            items = ['None']
        items = ', '.join(sorted(items))
        self.i_label = ttk.Label(self.frame, text=f'Items to bring for tomorrow: {items}', style='text.TLabel')
        self.i_label.grid(row=1, column=0, pady=5, sticky='w')

    def show_subject_menu(self, row, column):
        """Shows the subject menu whenever a subject is pressed"""
        global menu
        self.subject_clicked = [row, column]
        menu.subject_window(self.subject_clicked)

    def update_timetable(self):
        """Updates timetable"""
        Now1 = Timetable()
        Now1.Now_Subject()
        for row in range(1, 5 + 1):
            for period in range(1, len(Now.period_dict)):
                self.button_n[row][period].configure(text=Now1.timetable[row][period])
        self.i_label.destroy()
        self.view_item_list()

    def disable_buttons(self):
        """Disables Buttons To Prevent Multiple Menus"""
        for day in self.days:
            for period in self.periods:
                self.button_n[day][period]['state'] = 'disabled'

    def enable_buttons(self):
        """Enables Buttons from disabled state"""
        for day in self.days:
            for period in self.periods:
                self.button_n[day][period]['state'] = 'normal'


class Tk_Pg3:
    """All Function for page 3: Planner"""

    def __init__(self, master, pg_master):
        """Initializes Page 3"""
        self.root = master
        pg_master.rowconfigure(0, weight=1)
        pg_master.columnconfigure(0, weight=1)
        self.frame = ttk.Frame(window.page3, relief='raised', padding=10, style='main.TFrame')
        self.frame.grid(row=0, column=0, sticky='NSEW')
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=98)
        self.frame.columnconfigure(2, weight=1)
        self.buttons = []
        self.s_buttons = []
        self.menus = []
        self.calendars = []
        self.menu_buttons = []

        self.left_frame = ttk.Frame(self.frame, relief='raised', style='main.TFrame')
        self.left_frame.grid(row=0, column=0, sticky='news')
        self.left_frame.rowconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=19)

        self.m_frame = ttk.Frame(self.left_frame, padding=2, style='main.TFrame')
        self.m_frame.grid(row=0, column=0, padx=3, pady=3, sticky='nw')
        self.m_frame.rowconfigure(0, weight=1)
        self.menu_buttons.append(ttk.Button(self.m_frame, text='⬅', style='menu.TButton', width=2,
                                            command=self.hide_or_show_menu_tab))
        self.menu_buttons[-1].grid(row=0, column=0, padx=5, sticky='sw')
        self.m_label = ttk.Label(self.m_frame, text='Calendar Options', style='sub_heading.TLabel')
        self.m_label.grid(row=0, column=1, padx=2, sticky='sw')

        self.menu_f = ttk.Frame(self.left_frame, style='main.TFrame')
        self.menu_open = True
        self.mode = tk.StringVar(self.root, value='Monthly')

        self.mid_frame = ttk.Frame(self.frame, style='main.TFrame')
        self.mid_frame.grid(row=0, column=1, padx=3, pady=3, sticky='news')
        self.mid_frame.columnconfigure(0, weight=1)
        self.mid_frame.rowconfigure(0, weight=1)
        self.canvas = None
        self.c_frame = None
        self.week_frames = {}
        self.canvas_frame = ttk.Frame(self.mid_frame, style='main.TFrame')
        self.date_buttons = []
        self.n_label = ttk.Label()
        self.nf_label = ttk.Label()
        self.date = datetime.date.today()

        self.right_frame = ttk.Frame(self.frame, relief='raised', style='main.TFrame')
        self.right_frame.grid(row=0, column=2, sticky='news')
        self.right_frame.rowconfigure(0, weight=1)
        self.right_frame.rowconfigure(1, weight=19)

        self.i_frame = ttk.Frame(self.right_frame, padding=2, style='main.TFrame')
        self.i_frame.grid(row=0, column=0, padx=3, pady=3, sticky='ne')
        self.i_frame.rowconfigure(0, weight=1)
        self.menu_buttons.append(ttk.Button(self.i_frame, text='➡', style='menu.TButton', width=2,
                                            command=self.hide_or_show_item_tab))
        self.menu_buttons[-1].grid(row=0, column=1, padx=5, sticky='se')
        self.i_label = ttk.Label(self.i_frame, text='Schedules', style='sub_heading.TLabel')
        self.i_label.grid(row=0, column=0, padx=2, sticky='se')

        self.item_f = ttk.Frame(self.right_frame, style='main.TFrame')
        self.item_open = True

        self.menu_tab()
        self.schedule_tab()
        self.generate_calendar_from(datetime.date.today())
        self.root.bind('<Control-Key-e>', lambda e:
        self.event_menu('N/A', datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y'), 1))

    def menu_tab(self):
        self.menu_f.grid(row=1, column=0, padx=3, pady=3, sticky='wns')
        self.menu_f.columnconfigure(0, weight=1)
        self.menu_f.rowconfigure(0, weight=3)
        self.menu_f.rowconfigure(1, weight=1)
        self.menu_f.rowconfigure(2, weight=1)
        self.menu_f.rowconfigure(3, weight=1)

        calendar = Calendar(self.menu_f, selectmode='day',
                            year=self.date.year, month=self.date.month, day=self.date.day,
                            background=SQL.get_cus_setting_values_for("Heading")[0][4],
                            foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                            headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                            headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                            normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                            normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                            othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                            othermonthforeground=lighter_col(
                                lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                            othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                            othermonthweforeground=lighter_col(
                                lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                            weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                            weekendforeground=lighter_col(
                                lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                            selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                            selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                            )

        calendar.grid(row=0, column=0, pady=10, sticky='news')
        self.calendars.append(calendar)
        self.root.bind('<<CalendarSelected>>', lambda e: self.generate_calendar_from(calendar.get_date()))

        ttk.Label(self.menu_f, text=f'Today\'s Date: {datetime.date.today()}', style='text.TLabel') \
            .grid(row=1, column=0, sticky='nw')
        self.buttons.append(ttk.Button(self.menu_f, text='+ New Event', style='main.TButton',
                                       command=lambda: self.event_menu('N/A', calendar.get_date(), 1)))
        self.buttons[-1].grid(row=2, column=0, pady=5, sticky='news')
        calendar_options = ['Weekly', 'Monthly']
        self.menus.append(ttk.OptionMenu(self.menu_f, self.mode, self.mode.get(), *calendar_options,
                                         command=lambda e: self.generate_calendar_from(calendar.get_date())))
        self.menus[-1].grid(row=3, column=0, pady=5)

    def hide_or_show_menu_tab(self):
        self.buttons = []
        self.menus = []
        self.calendars = []
        if self.menu_open:
            self.menu_f.destroy()
            self.m_label.configure(text='')
            self.menu_open = False
        else:
            self.menu_f = ttk.Frame(self.left_frame, style='main.TFrame')
            self.m_label.configure(text='Calendar Options')
            self.menu_tab()
            self.menu_open = True

    def schedule_tab(self):
        global SQL
        self.item_f = ttk.Frame(self.right_frame, style='main.TFrame')
        self.item_f.grid(row=1, column=0, padx=3, sticky='en')

        subject_frame = ttk.Frame(self.item_f, style='main.TFrame')
        subject_frame.grid(row=0, column=0, padx=3, pady=1, sticky='news')

        ttk.Label(subject_frame, text='Tasks Not Added:', style='text.TLabel') \
            .grid(row=0, column=0, columnspan=2, pady=3, sticky='w')

        canvas = tk.Canvas(subject_frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                           height=70, width=220, highlightthickness=0)

        y_scroll = ttk.Scrollbar(subject_frame, orient='vertical', command=canvas.yview)
        y_scroll.grid(row=1, column=1, sticky='ns')

        canvas.configure(yscrollcommand=y_scroll.set)
        canvas.grid(row=1, column=0, sticky='news')
        c_frame = ttk.Frame(canvas, style='main.TFrame')
        canvas.create_window((0, 0), window=c_frame, anchor='nw')
        c_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        self.s_buttons = []
        counter = 0
        for i in assignment:
            event = SQL.get_events_with_oid(i)
            proceed = False
            if assignment[i].main_task:
                proceed = True
            elif assignment[i].group == 'N/A':
                proceed = True
            if not event and proceed:
                self.s_buttons.append(
                    ttk.Button(c_frame, text=assignment[i].name, style='list.TButton',
                               command=lambda l=i: self.event_menu(assignment[l].id,
                                                                   datetime.date.today().strftime('%d/%m/%Y'), 1)))
                self.s_buttons[-1].grid(row=i, column=0, padx=3, pady=1, sticky='w')
                counter += 1
        if counter == 0:
            ttk.Label(c_frame, text='None', style='sub_heading.TLabel').grid(row=0, column=0)

        r_frame = ttk.Frame(self.item_f, style='main.TFrame')
        r_frame.grid(row=1, column=0, padx=2, pady=1, sticky='news')
        ttk.Label(r_frame, text='Recommended Schedule\nFor Today:', style='text.TLabel') \
            .grid(row=0, column=0, pady=2, sticky='w')

        canvas1 = tk.Canvas(r_frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                            height=200, width=220, highlightthickness=0)

        y_scroll1 = ttk.Scrollbar(r_frame, orient='vertical', command=canvas1.yview)
        y_scroll1.grid(row=1, column=1, sticky='ns')

        canvas1.configure(yscrollcommand=y_scroll1.set)
        canvas1.grid(row=1, column=0, sticky='news')
        t_frame = ttk.Frame(canvas1, style='main.TFrame')
        canvas1.create_window((0, 0), window=t_frame, anchor='nw')
        t_frame.bind('<Configure>', lambda e: canvas1.configure(scrollregion=canvas1.bbox('all')))
        ttk.Button(self.item_f, text='Apply for Today', style='main.TButton') \
            .grid(row=2, column=0, padx=1, sticky='news')

    def hide_or_show_item_tab(self):
        if self.item_open:
            self.item_f.destroy()
            self.i_label.configure(text='')
            self.item_open = False
        else:
            self.item_f = ttk.Frame(self.left_frame, style='main.TFrame')
            self.i_label.configure(text='Schedules')
            self.schedule_tab()
            self.item_open = True

    def generate_calendar_from(self, date):
        try:
            self.mid_frame.destroy()
            self.canvas.destroy()
            self.c_frame.destroy()
        except AttributeError:
            pass
        self.date_buttons = []
        self.mid_frame = ttk.Frame(self.frame, style='main.TFrame')
        self.mid_frame.grid(row=0, column=1, padx=3, pady=3, sticky='news')
        self.mid_frame.rowconfigure(0, weight=1)
        self.mid_frame.columnconfigure(0, weight=1)

        frame1 = ttk.Frame(self.mid_frame, padding=1, style='main.TFrame')
        frame1.grid(row=0, column=0, sticky='news')
        frame1.rowconfigure(0, weight=1)
        frame1.columnconfigure(0, weight=1)
        try:
            self.date = datetime.datetime.strptime(str(date), '%m/%d/%y')
        except ValueError:
            try:
                self.date = datetime.datetime.strptime(str(date), '%Y-%m-%d')
            except ValueError:
                pass
        if self.mode.get() == 'Monthly':
            self.canvas_frame.destroy()
            self.canvas_frame = self.show_monthly_calendar(frame1, self.date)
        if self.mode.get() == 'Weekly':
            self.canvas_frame.destroy()
            self.canvas_frame = self.show_weekly_calendar(frame1, 7, self.date)

    def show_monthly_calendar(self, frame1, date):
        m_frame = ttk.Frame(frame1, style='main.TFrame')
        m_frame.grid(row=0, column=0, sticky='news')
        m_frame.rowconfigure(0, weight=99)
        m_frame.rowconfigure(1, weight=1)
        m_frame.columnconfigure(0, weight=99)
        m_frame.columnconfigure(1, weight=1)
        self.canvas = tk.Canvas(m_frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                                height=90, width=220, highlightthickness=0)

        y_scroll = ttk.Scrollbar(m_frame, orient='vertical', command=self.canvas.yview)
        y_scroll.grid(row=0, column=1, sticky='ns')

        x_scroll = ttk.Scrollbar(m_frame, orient='horizontal', command=self.canvas.xview)
        x_scroll.grid(row=1, column=0, sticky='we')

        self.canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.canvas.grid(row=0, column=0, sticky='news')
        c_frame = ttk.Frame(self.canvas, style='main.TFrame')
        self.c_frame = self.canvas.create_window((0, 0), window=c_frame, anchor='nw')
        c_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', self.resize_frame)
        # c_frame.pack(expand=1, fill='both') # THIS TOOK ME 1 WHOLE HOUR To REALIZE AND FIX
        # I'm So Mad. It's 11:40pm, so I should now rest. ALL I NEEDED TO DO IS DELETE THIS LINE YOU JOKING

        for i in range(1, 6):
            c_frame.rowconfigure(i, weight=3)
        for i in range(0, 7):
            frame = ttk.Frame(c_frame, relief='sunken', padding=2, style='main.TFrame')
            frame.grid(row=0, column=i, sticky='news')
            day_dict = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
            ttk.Label(frame, text=day_dict[i + 1], style='Schedule.TLabel').pack(anchor='w')
            c_frame.columnconfigure(i, weight=2)
        temp_date = date
        date -= datetime.timedelta(days=date.day - 1)
        date -= datetime.timedelta(days=date.weekday())
        for j in range(1, 6):
            for i in range(0, 7):
                frame = ttk.Frame(c_frame, relief='raised', padding=3, style='main.TFrame')
                frame.grid(row=j, column=i, sticky='news')
                if date == temp_date:
                    style = 'now_date.TButton'
                elif date.month != temp_date.month:
                    style = 'dim_date.TButton'
                else:
                    style = 'date.TButton'
                if date.day == 1:
                    self.date_buttons.append(
                        ttk.Button(frame, text=f'{date.day}/{str(date.month).zfill(2)}', style=style,
                                   command=lambda x=date.day, y=date.month, z=date.year:
                                   self.event_menu('N/A', f'{x}/{y}/{z}', 0)))
                    self.date_buttons[-1].grid(row=0, column=0, sticky='news')
                else:
                    self.date_buttons.append(
                        ttk.Button(frame, text=str(date.day), style=style,
                                   command=lambda x=date.day, y=date.month, z=date.year:
                                   self.event_menu('N/A', f'{x}/{y}/{z}', 0)))
                    self.date_buttons[-1].grid(row=0, column=0, sticky='news')
                canvas = tk.Canvas(frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                                   height=45, width=3, highlightthickness=0)

                y_scroll = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)

                canvas.configure(yscrollcommand=y_scroll.set)
                canvas.grid(row=1, column=0, sticky='news')
                frame1 = ttk.Frame(canvas, style='main.TFrame')
                canvas.create_window((0, 0), window=frame1, anchor='nw')
                event = SQL.get_events_in_date(str(datetime.datetime.strftime(date, '%d/%m/%Y')))
                for k in range(0, len(event)):
                    ttk.Label(frame1, text=event[k][0], style=f'{event[k][6]}.TLabel').grid(row=k, column=0)
                date += datetime.timedelta(days=1)
        return m_frame

    def show_weekly_calendar(self, frame1, columns: int, date):
        frame_m = ttk.Frame(frame1, style='main.TFrame')
        frame_m.grid(row=0, column=0, sticky='news')
        frame_m.rowconfigure(0, weight=1)
        frame_m.rowconfigure(1, weight=98)
        frame_m.rowconfigure(2, weight=1)
        frame_m.columnconfigure(0, weight=1)
        frame_m.columnconfigure(1, weight=98)
        frame_m.columnconfigure(2, weight=1)

        t_canvas = tk.Canvas(frame_m, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                             height=90, width=40, highlightthickness=0)
        t_canvas.grid(row=1, column=0, sticky='news')
        frame_t = ttk.Frame(t_canvas, style='main.TFrame')
        t_canvas.create_window((0, 0), window=frame_t, anchor='nw')
        frame_t.bind('<Configure>', lambda e: t_canvas.configure(scrollregion=t_canvas.bbox('all')))

        d_canvas = tk.Canvas(frame_m, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                             height=25, width=220, highlightthickness=0)
        d_canvas.grid(row=0, column=1, sticky='news')
        frame_d = ttk.Frame(d_canvas, style='main.TFrame')
        d_canvas.create_window((0, 0), window=frame_d, anchor='nw')
        frame_d.bind('<Configure>', lambda e: d_canvas.configure(scrollregion=d_canvas.bbox('all')))

        canvas = tk.Canvas(frame_m, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                           height=90, width=220, highlightthickness=0)
        canvas.grid(row=1, column=1, sticky='news')
        frame1 = ttk.Frame(canvas, style='main.TFrame')
        canvas.create_window((0, 0), window=frame1, anchor='nw')
        frame1.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        def xview(*args):
            d_canvas.xview(*args)
            canvas.xview(*args)

        def yview(*args):
            t_canvas.yview(*args)
            canvas.yview(*args)

        y_scroll = ttk.Scrollbar(frame_m, orient='vertical', command=yview)
        y_scroll.grid(row=0, column=2, rowspan=2, sticky='ns')

        x_scroll = ttk.Scrollbar(frame_m, orient='horizontal', command=xview)
        x_scroll.grid(row=2, column=0, columnspan=2, sticky='we')
        t_canvas.configure(yscrollcommand=y_scroll.set)
        d_canvas.configure(xscrollcommand=x_scroll.set)
        canvas.configure(yscrollcommand=y_scroll.set)
        canvas.configure(xscrollcommand=x_scroll.set)

        def set_canvas_region():
            canvas.xview_moveto(x_region)
            canvas.yview_moveto(y_region)

        orig_date = date
        date -= datetime.timedelta(days=date.weekday())
        time = datetime.datetime.now()

        if not datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()) == date.date():
            time -= datetime.timedelta(minutes=time.hour * 60 + time.minute)
        x_region = 0.1429 * orig_date.weekday()
        y_region = (time.hour * 60 + time.minute - 60) / 1440

        d_canvas.bind("<Configure>", lambda e: d_canvas.xview_moveto(x_region))
        canvas.bind("<Configure>", lambda e: set_canvas_region())
        t_canvas.bind("<Configure>", lambda e: t_canvas.yview_moveto(y_region))

        height = 60
        width = 150

        for i in range(0, 24):
            frame = ttk.Frame(frame_t, relief='raised', padding=1, width=40, height=height, style='main.TFrame')
            frame.grid(row=i, column=0)
            frame.pack_propagate(False)
            ttk.Label(frame, text=f'{str(i).zfill(2)}:00', style='Schedule.TLabel').pack(anchor='nw')

        for i in range(0, columns):
            temp_date = datetime.datetime.strftime(date, '%a\t%d %B')
            frame = ttk.Frame(frame_d, relief='sunken', padding=2, width=width, height=25, style='main.TFrame')
            frame.grid(row=0, column=i)
            frame.pack_propagate(False)
            if orig_date == date:
                style = 'now_date.TButton'
            else:
                style = 'date.TButton'
            self.date_buttons.append(ttk.Button(frame, text=f'{temp_date}',
                                                command=lambda x=date.day, y=date.month, z=date.year:
                                                self.event_menu('N/A', f'{x}/{y}/{z}', 1), style=style))
            self.date_buttons[-1].pack(anchor='w')

            for j in range(0, 24):
                frame = ttk.Frame(frame1, relief='groove', padding=1, width=width, height=height, style='main.TFrame')
                frame.grid(row=j, column=i)
                frame.pack_propagate(False)
                frame2 = ttk.Frame(frame, relief='raised', style='main.TFrame')
                frame2.pack(expand=1, fill='both')
                frame2.rowconfigure(0, weight=1)
                frame2.columnconfigure(0, weight=1)
                frame2.columnconfigure(1, weight=19)
                self.week_frames[f'0,{j},{i}'] = ttk.Frame(frame2, relief='flat', padding=1, style='main.TFrame')
                self.week_frames[f'0,{j},{i}'].grid(row=0, column=0, sticky='news')
                ttk.Label(self.week_frames[f'0,{j},{i}'], text='', style='text.TLabel').grid(row=0, column=0, padx=1)
                self.week_frames[f'1,{j},{i}'] = ttk.Frame(frame2, relief='flat', padding=1, style='main.TFrame')
                self.week_frames[f'1,{j},{i}'].grid(row=0, column=1, sticky='news')
                self.week_frames[f'1,{j},{i}'].columnconfigure(0, weight=1)
                events = 0
                event_held = 0
                for event in event_:
                    n_event = event_[event]
                    temp_date = date
                    temp_date += datetime.timedelta(hours=1)
                    if n_event.start_date < date < n_event.end_date:
                        if date < n_event.end_date < temp_date:
                            frame2.columnconfigure(0, weight=event_held * 2)
                            ttk.Frame(self.week_frames[f'0,{j},{i}'], style=f'{n_event.color}.TFrame') \
                                .place(x=event_held * 6, y=0, height=int(n_event.end_date.minute), width=6)
                            event_held += 1
                        else:
                            frame2.columnconfigure(0, weight=event_held * 2)
                            ttk.Frame(self.week_frames[f'0,{j},{i}'], style=f'{n_event.color}.TFrame') \
                                .place(x=event_held * 6, y=0, height=60, width=6)
                            event_held += 1
                for event in event_:
                    n_event = event_[event]
                    temp_time = date
                    temp_time += datetime.timedelta(hours=1)
                    if date <= n_event.start_date < temp_time:
                        self.week_frames[f'1,{j},{i}'].rowconfigure(events, weight=1)
                        self.date_buttons.append(ttk.Button(self.week_frames[f'1,{j},{i}'], text=n_event.name,
                                                            style=f'{n_event.color}.TButton',
                                                            command=lambda l=n_event.id: menu.event_window(l)))
                        self.date_buttons[-1].grid(row=events, column=0, sticky='news')
                        if (n_event.end_date - n_event.start_date).total_seconds() / 60.0 < 60:
                            set_height = (n_event.end_date - n_event.start_date).total_seconds() / 60.0
                            if (n_event.end_date - n_event.start_date).total_seconds() < 20:
                                set_height = 20
                        else:
                            set_height = (temp_time - n_event.start_date).total_seconds() / 60.0
                        frame2.columnconfigure(0, weight=event_held * 2)
                        ttk.Frame(self.week_frames[f'0,{j},{i}'], style=f'{n_event.color}.TFrame') \
                            .place(x=event_held * 6, y=n_event.start_date.minute, height=int(set_height), width=6)
                        events += 1
                        event_held += 1
                    elif n_event.start_date < date <= n_event.end_date and i == 0 and j == 0:
                        self.week_frames[f'1,{j},{i}'].rowconfigure(events, weight=1)
                        self.date_buttons.append(ttk.Button(self.week_frames[f'1,{j},{i}'], text=n_event.name,
                                                            style=f'{n_event.color}.TButton',
                                                            command=lambda l=n_event.id: menu.event_window(l)))
                        self.date_buttons[-1].grid(row=events, column=0, sticky='news')
                        events += 1
                date += datetime.timedelta(hours=1)

        self.tick_time(frame_t, frame1, width, columns, orig_date)
        return frame_m

    def tick_time(self, frame_t, frame, width, column, date):
        """Ticks the time in the app for notifications and time changes"""
        global event_
        self.n_label.destroy()
        self.nf_label.destroy()
        time = datetime.datetime.now()
        self.n_label = ttk.Label(frame_t, text=f'{str(time.hour).zfill(2)}:{str(time.minute).zfill(2)}------',
                                 style='now_date.TLabel')
        self.n_label.place(x=0, y=time.hour * 60 + time.minute - 1, anchor='w', width=40)
        text = ''
        if not abs(int(time.date().strftime('%W')) - int(date.date().strftime('%W'))) > 0:
            for i in range(0, int(math.floor(width / 7 * time.weekday()))):
                text = ''.join([text, '- '])
            for i in range(0, int(math.floor(width / 4))):
                text = ''.join([text, '-'])
            for i in range(0, int(math.floor(width / 6.8 * (column - time.weekday() - 1)))):
                text = ''.join([text, '- '])
        else:
            for i in range(0, int(math.floor(width / 6.8 * column))):
                text = ''.join([text, '- '])
        self.nf_label = ttk.Label(frame, text=f'{text}', style='now_date.TLabel')
        self.nf_label.place(x=0, y=time.hour * 60 + time.minute - 1, anchor='w', width=width * column)

        self.n_label.after((60 - datetime.datetime.now().second) * 1000 +
                           int(1000 - round(datetime.datetime.now().microsecond / 1000)),
                           lambda: self.tick_time(frame_t, frame, width, column, date))

    def resize_frame(self, event):
        if self.mode.get() == 'Monthly':
            width = event.width
            if int(SQL.get_cus_setting_values_for('Schedule')[0][2]) < 9:
                adder = 0.4
            else:
                adder = 0
            b_width = int(math.floor(width / (64.6 + adder)))
            height = event.height
            self.canvas.itemconfig(self.c_frame, width=width, height=height)
            for button in self.date_buttons:
                try:
                    button.configure(width=b_width)
                except tkinter.TclError:
                    pass

    def event_menu(self, orig_id, date, mode: int):
        """Shows the event menu whenever something is pressed"""
        global menu
        if not menu.tabs > 0:
            if mode == 0:
                event = SQL.get_events_in_date(date)
                if len(event) == 0:
                    menu.new_event_window(orig_id, date)
                else:
                    menu.date_window(date)
            else:
                menu.new_event_window(orig_id, date)

    def update(self):
        """Updates This Page"""
        self.generate_calendar_from(self.date)
        if self.item_open:
            self.item_f.destroy()
            self.schedule_tab()

    def disable_buttons(self):
        for button in self.menu_buttons:
            button['state'] = 'disabled'
        for button in self.buttons:
            button['state'] = 'disabled'
        for button in self.s_buttons:
            try:
                button['state'] = 'disabled'
            except tkinter.TclError:
                continue
        for button in self.date_buttons:
            button['state'] = 'disabled'
        for n_menu in self.menus:
            n_menu['state'] = 'disabled'
        for button in self.calendars:
            button['state'] = 'disabled'

    def enable_buttons(self):
        for button in self.menu_buttons:
            button['state'] = 'normal'
        for button in self.buttons:
            button['state'] = 'normal'
        for button in self.s_buttons:
            try:
                button['state'] = 'normal'
            except tkinter.TclError:
                continue
        for button in self.date_buttons:
            button['state'] = 'normal'
        for n_menu in self.menus:
            n_menu['state'] = 'normal'
        for button in self.calendars:
            button['state'] = 'normal'


class Tk_Pg4:
    """Functions and setup for Page4, Settings"""

    def __init__(self, master, pg_master):
        """Initializes Page 4"""
        self.root = master
        pg_master.rowconfigure(0, weight=1)
        pg_master.columnconfigure(0, weight=1)
        self.variables = {}

        self.frame = ttk.Frame(window.page4, relief='raised', padding=10, style='main.TFrame')
        self.frame.grid(row=0, column=0, sticky='NSEW')
        self.frame.rowconfigure(0, weight=19)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=2)
        self.frame.columnconfigure(0, weight=2)
        self.frame.columnconfigure(1, weight=19)
        self.frame.columnconfigure(2, weight=1)
        canvas = tk.Canvas(self.frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                           height=310, width=420, highlightthickness=0)
        y_scroll = ttk.Scrollbar(self.frame, orient='vertical', command=canvas.yview)
        y_scroll.grid(row=0, column=2, sticky='ns')

        x_scroll = ttk.Scrollbar(self.frame, orient='horizontal', command=canvas.xview)
        x_scroll.grid(row=1, column=0, sticky='we', columnspan=2)

        canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        canvas.grid(row=0, column=0, sticky='news', columnspan=2, padx=1, pady=1)
        self.cur_frame = ttk.Frame(canvas, style='main.TFrame')
        canvas.create_window((0, 0), window=self.cur_frame, anchor='nw')
        self.cur_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        self.cur_window = ttk.Frame(self.cur_frame, style='main.TFrame')
        self.back_button = ttk.Button(self.frame, text='⬅', style='menu.TButton', width=2, command=self.main_window)
        self.back_button.grid(row=2, column=0, padx=2, pady=2, sticky='sw')
        self.main_window()

    def main_window(self):
        """Main Settings Window"""
        self.cur_window.destroy()
        self.back_button['state'] = 'disabled'
        self.cur_window = ttk.Frame(self.cur_frame, relief='flat', style='main.TFrame')
        self.cur_window.pack(expand=1, fill='both')
        self.cur_window.rowconfigure(0, weight=1)
        self.cur_window.rowconfigure(1, weight=3)

        ttk.Label(self.cur_window, text='Settings', style='sub_heading.TLabel').grid(row=0, column=0, sticky='nw')
        frame_c = ttk.Frame(self.cur_window, relief='raised', style='main.TFrame', padding=2)
        frame_c.grid(row=1, column=0, padx=2, pady=2, sticky='nw')
        ttk.Button(frame_c, text='Customization', command=lambda: self.go_to_menu('Customization'),
                   style='main.TButton').grid(row=0, column=0, sticky='ew')
        ttk.Label(frame_c, text='Customize different widgets and \ntheir color, font, fontsize', style='text.TLabel') \
            .grid(row=1, column=0, pady=2)

    def go_to_menu(self, tab):
        """Travelling to Different Menus"""
        self.cur_window.destroy()
        self.back_button['state'] = 'normal'
        if tab == 'Customization':
            self.customization_tab()

    def customization_tab(self):
        """Functions for Customization"""
        self.cur_window = ttk.Frame(self.cur_frame, relief='raised', style='main.TFrame', padding=1)
        self.cur_window.pack(expand=1, fill='both')
        self.cur_window.rowconfigure(0, weight=2)
        fonts = []
        clicked_fonts = set()
        for i in range(1, 10):
            self.cur_window.rowconfigure(i, weight=4)
        ttk.Label(self.cur_window, text='Customization Settings', style='sub_heading.TLabel') \
            .grid(row=0, column=0, padx=2, pady=1, columnspan=3)
        widgets = [['Theme', 'theme'], ['Headings', 'Heading'], ['Sub Headings', 'Sub_Heading'],
                   ['Buttons', 'Main_Button'], ['Text', 'Text'], ['Timetable Text', 'Timetable'],
                   ['Calendar Text', 'Schedule'], ['Background', 'Frame'], ['Treeview', 'Treeview'],
                   ["Today's Color", 'Now_Date']]
        for value, name in enumerate(widgets):
            ttk.Label(self.cur_window, text=f'{name[0]}:', style='text.TLabel') \
                .grid(row=value + 1, column=0, sticky='w', padx=1)
            cols = 1
            for typing, content in enumerate(SQL.get_cus_setting_values_for(name[1])[0]):
                first_color = value == 7 or value == 1 or value == 9
                if typing == 0 or content == '':
                    continue
                if typing == 1 and not value == 9:
                    if name[1] == 'theme':
                        self.variables[f'{name[1]}'] = tk.StringVar(self.root, value=content)
                        ttk.OptionMenu(self.cur_window, self.variables[f'{name[1]}'],
                                       self.variables[f'{name[1]}'].get(),
                                       *ttk.Style().theme_names()) \
                            .grid(row=value + 1, column=cols, sticky='news', padx=1)
                        continue
                    f_frame = ttk.Frame(self.cur_window, style='main.TFrame', relief='flat')
                    f_frame.grid(row=value + 1, column=cols, sticky='news', padx=1)
                    ttk.Label(f_frame, text='font:', style='text.TLabel').grid(row=0, column=0)
                    self.variables[f'{name[1]}_font'] = tk.StringVar(self.root, value=content)

                    def init_OptionMenu(menu_number):
                        option_menu = fonts[menu_number]
                        clicked = menu_number in clicked_fonts
                        if not clicked:
                            for item in range(0, int(option_menu['menu'].index('end'))):
                                option_menu['menu'].entryconfig(item,
                                                                font=tk.font.Font(family=tk.font.families()[item]))
                            clicked_fonts.add(menu_number)

                    fonts.append(
                        ttk.OptionMenu(f_frame, self.variables[f'{name[1]}_font'],
                                       self.variables[f'{name[1]}_font'].get(),
                                       *tk.font.families()))
                    fonts[-1].grid(row=0, column=1)
                    fonts[-1].bind('<ButtonPress>', lambda e, v=int(len(fonts) - 1): init_OptionMenu(v))

                    cols += 1
                    continue
                elif typing == 2 and not value == 9:
                    fs_frame = ttk.Frame(self.cur_window, style='main.TFrame', relief='flat')
                    fs_frame.grid(row=value + 1, column=cols, sticky='news', padx=1)
                    ttk.Label(fs_frame, text='Fontsize:', style='text.TLabel').grid(row=0, column=0)
                    self.variables[f'{name[1]}_fontsize'] = tk.IntVar(self.root, value=int(content))
                    ttk.Spinbox(fs_frame, from_=3, to=25, textvariable=self.variables[f'{name[1]}_fontsize'], width=3) \
                        .grid(row=0, column=1, padx=2)
                    cols += 1
                    continue
                elif typing == 3 and first_color:
                    bg_frame = ttk.Frame(self.cur_window, style='main.TFrame', relief='flat')
                    bg_frame.grid(row=value + 1, column=cols, sticky='news', padx=1)
                    ttk.Label(bg_frame, text='Color:', style='text.TLabel').grid(row=0, column=0)
                    self.variables[f'{name[1]}_color'] = tk.StringVar(self.root, value=content)
                    col = content

                    def color_chooser(color, var):
                        orig_color = color
                        color = askcolor(color=orig_color.get(), title="Choose a Color")
                        if color[1] is not None:
                            color = str(color[1])
                            window.style.configure(f'{color}l.TButton', foreground=f'{lighter_col(color, 1)}',
                                                   font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                            window.style.map(f'{color}l.TButton', background=[('!active', f'{color}'),
                                                                              ('active', lighter_col(color, 1.1))])
                            self.variables[f'{var}_col_button'].config(text=color, style=f'{color}l.TButton')
                            self.variables[f'{var}_color'].set(str(color))
                        else:
                            self.variables[f'{var}_color'].set(orig_color)

                    window.style.configure(f'{col}l.TButton', foreground=f'{lighter_col(col, 1)}',
                                           font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                    window.style.map(f'{col}l.TButton', background=[('!active', f'{col}'),
                                                                    ('active', lighter_col(col, 1.1))])
                    self.variables[f'{name[1]}_col_button'] = ttk.Button(bg_frame, text=col, style=f'{col}l.TButton',
                                                                         command=lambda x=name[1]: color_chooser(
                                                                             self.variables[f'{x}_color'], x))
                    self.variables[f'{name[1]}_col_button'].grid(row=0, column=1, padx=2)
                    cols += 1
                    continue
                elif typing == 4:
                    bg2_frame = ttk.Frame(self.cur_window, style='main.TFrame', relief='flat')
                    bg2_frame.grid(row=value + 1, column=cols, sticky='news', padx=1)
                    ttk.Label(bg2_frame, text='Background color:', style='text.TLabel').grid(row=0, column=0)
                    self.variables[f'{name[1]}_color2'] = tk.StringVar(self.root, value=content)
                    col = content

                    def color_chooser2(color, var):
                        orig_color = color
                        color = askcolor(color=orig_color.get(), title="Choose a Color")
                        if color[1] is not None:
                            color = str(color[1])
                            window.style.configure(f'{color}l.TButton', foreground=f'{lighter_col(color, 1)}',
                                                   font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                            window.style.map(f'{color}l.TButton', background=[('!active', f'{color}'),
                                                                              ('active', lighter_col(color, 1.1))])
                            self.variables[f'{var}_col_button2'].config(text=color, style=f'{color}l.TButton')
                            self.variables[f'{var}_color2'].set(str(color))
                        else:
                            self.variables[f'{var}_color2'].set(orig_color)

                    window.style.configure(f'{col}l.TButton', foreground=f'{lighter_col(col, 1)}',
                                           font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                    window.style.map(f'{col}l.TButton', background=[('!active', f'{col}'),
                                                                    ('active', lighter_col(col, 1.1))])
                    self.variables[f'{name[1]}_col_button2'] = ttk.Button(bg2_frame, text=col, style=f'{col}l.TButton',
                                                                          command=lambda x=name[1]: color_chooser2(
                                                                              self.variables[f'{x}_color2'], x))
                    self.variables[f'{name[1]}_col_button2'].grid(row=0, column=1, padx=2)
                    cols += 1
                    continue
                elif typing == 5:
                    tr_frame = ttk.Frame(self.cur_window, style='main.TFrame', relief='flat')
                    tr_frame.grid(row=value + 1, column=cols, sticky='news', padx=1)
                    ttk.Label(tr_frame, text='Treeview Row Height:', style='text.TLabel').grid(row=0, column=0)
                    self.variables[f'{name[1]}_row_height'] = tk.IntVar(self.root, value=int(content))
                    ttk.Spinbox(tr_frame, from_=15, to=50, textvariable=self.variables[f'{name[1]}_row_height'],
                                width=3) \
                        .grid(row=0, column=1, padx=2)
                    cols += 1
        ttk.Label(self.cur_window, text='To Change Background Image, Drag an Image into the Images folder and'
                                        'name the image as background1,\nreplace the existing background1 image',
                  style='text.TLabel').grid(row=len(widgets) + 1, column=0, columnspan=5, padx=1, pady=3)
        ttk.Button(self.cur_window, text='Reset To Default and Exit', style='main.TButton',
                   command=self.cus_settings_reset_to_default) \
            .grid(row=len(widgets) + 2, column=0, columnspan=3, sticky='news', padx=1, pady=2)
        ttk.Button(self.cur_window, text='Apply and Exit', style='main.TButton', command=self.cus_settings_apply) \
            .grid(row=len(widgets) + 2, column=3, columnspan=2, sticky='news', padx=1, pady=2)

    def cus_settings_reset_to_default(self):
        """Reset to Default Customization Settings"""
        global SQL
        SQL.reset_cus_setting_values()
        self.root.destroy()

    def cus_settings_apply(self):
        """Applies Changes Made in Customization Settings"""
        global SQL
        SQL.modify_cus_setting_values_for('theme', self.variables['theme'].get(), '', '', '', '')
        SQL.modify_cus_setting_values_for('Heading', self.variables['Heading_font'].get(),
                                          self.variables['Heading_fontsize'].get(),
                                          self.variables['Heading_color'].get(),
                                          self.variables['Heading_color2'].get(), '')
        SQL.modify_cus_setting_values_for('Sub_Heading', self.variables['Sub_Heading_font'].get(),
                                          self.variables['Sub_Heading_fontsize'].get(),
                                          self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Main_Button', self.variables['Main_Button_font'].get(),
                                          self.variables['Main_Button_fontsize'].get(),
                                          self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Text', self.variables['Text_font'].get(),
                                          self.variables['Text_fontsize'].get(),
                                          self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Timetable', self.variables['Timetable_font'].get(),
                                          self.variables['Timetable_fontsize'].get(),
                                          self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Schedule', self.variables['Schedule_font'].get(),
                                          self.variables['Schedule_fontsize'].get(),
                                          self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Frame', '', '', self.variables['Frame_color'].get(), '', '')
        SQL.modify_cus_setting_values_for('Treeview', self.variables['Treeview_font'].get(),
                                          self.variables['Treeview_fontsize'].get(),
                                          self.variables['Frame_color'].get(),
                                          self.variables['Treeview_color2'].get(),
                                          self.variables['Treeview_row_height'].get())
        SQL.modify_cus_setting_values_for('Now_Date', self.variables['Schedule_font'].get(),
                                          self.variables['Schedule_fontsize'].get(),
                                          self.variables['Now_Date_color'].get(), '', '')
        self.root.destroy()


class Tk_Sub_Pages:
    """Functions for different pop-up windows in Tkinter GUI"""

    def __init__(self):
        """Initialization of sub-pages"""
        self.root = {}
        self.tab = {}
        self.tabs = 0
        self.disable_tabs = []

    def update_disables(self):
        """Updates disable tabs"""
        global window
        self.disable_tabs, page = window.get_disable_notebook_tabs()
        window_pages = (window.pg1, window.pg2, window.pg3, window.pg4)
        window_pages[page].disable_buttons()
        window.disable_notebook(self.disable_tabs)

    def new_task_window(self):
        """Functions for writing new task window"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Task Database")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_NTask(root1, 'N/A', False, 0)

    def task_window(self, task_id: int):
        """Functions for the task windows"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Task Settings")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Task(root1, task_id)

    def subject_window(self, subject_info: list):
        """Functions for the subject windows"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Subject Settings")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Subject(root1, subject_info)

    def timetable_window(self):
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+110+60")
        root1.title("Modify Timetable Pattern")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Timetable(root1)

    def new_event_window(self, orig_id, date):
        """Functions for the new event window"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("New Event")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_NEvent(root1, orig_id, date)

    def date_window(self, date):
        """Functions for the new date window"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Events List")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Date(root1, date)

    def event_window(self, event_id: int):
        """Functions for event window"""
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Event Settings")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Event(root1, event_id)

    def notification_window(self):
        root1 = tk.Toplevel()
        root1.attributes('-topmost', 'true')
        self.root[self.tabs] = root1
        root1.geometry("+240+90")
        root1.title("Notifications")
        self.update_disables()
        self.tabs += 1
        self.tab[self.tabs] = Tk_Sub_Notify(root1)

    def send_all_back(self):
        for tab in self.tab:
            self.tab[tab].root.attributes('-topmost', 'false')

    def send_all_forward(self):
        for tab in self.tab:
            self.tab[tab].root.attributes('-topmost', 'true')


class Tk_Sub_NTask:
    """Functions in write new task menu"""

    def __init__(self, master, group, update: bool, task_id):
        """Initializes a new task menu"""
        self.root = master
        self.root.attributes('-topmost', 'true')
        self.group = group
        self.update = update
        self.id = task_id
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()
        self.w_frame = ttk.Frame(self.frame, relief='raised', padding=10, style='main.TFrame')
        self.w_frame.grid(row=1, column=0, columnspan=2, sticky='news')

        # TITLE
        ttk.Label(self.frame, text='Write New Task', style='sub_heading.TLabel') \
            .grid(row=0, column=0, columnspan=2, padx=20, pady=5)

        self.subject = tk.StringVar()
        self.task = tk.StringVar()
        self.date = tk.StringVar()
        self.state = tk.StringVar()
        self.date_c = None
        self.te_label = None
        self.t_ERROR = ''
        self.write_menu()

        ttk.Button(self.frame, text="Submit", command=self.submit, style='main.TButton') \
            .grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        ttk.Button(self.frame, text="Cancel", command=self.destroy_window, style='main.TButton') \
            .grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.root.bind('<Return>', lambda e: self.submit())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def write_menu(self):
        """Initializes Writing Menu For a New Task"""
        global Now
        Now = Timetable()
        Now.Now_Subject()
        ttk.Label(self.w_frame, text="Input Subject:", style='text.TLabel').grid(row=1, column=0, padx=5, pady=10)
        subject_now = Now.Now_Subject()
        s_set = {Now.line1, Now.line2, Now.line3, Now.line4, Now.line5, Now.line6, Now.line7, Now.line8, Now.line9}
        s_options = []
        for i in s_set:
            s_options.append(i)
        sorting_items(Important)
        s_options = sorted(s_options, key=lambda x: subject_sort[x])
        ttk.OptionMenu(self.w_frame, self.subject, str(subject_now), *s_options) \
            .grid(row=1, column=1, padx=5, pady=10, columnspan=2)

        # TASK LABEL AND ENTRY
        ttk.Label(self.w_frame, text="Input Task:", style='text.TLabel').grid(row=2, column=0, padx=5, pady=1)
        ttk.Entry(self.w_frame, textvariable=self.task, width=50).grid(row=2, column=1, padx=5, pady=1)

        # DATE LABEL AND ENTRY
        ttk.Label(self.w_frame, text="Input Date:", style='text.TLabel').grid(row=4, column=0, padx=5, pady=5)
        self.date_c = DateEntry(self.w_frame, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1))
        self.date_c.grid(row=4, column=1, padx=5, pady=5)

        # STATE LABEL AND OptionMenu
        ttk.Label(self.w_frame, text="Input State:", style='text.TLabel').grid(row=5, column=0, padx=5, pady=10)
        r_state = main_state_list[3]
        sa_options = []
        for states in range(0, int(len(main_state_list) / 2)):
            sa_options.append(main_state_list[states + 1])
        ttk.OptionMenu(self.w_frame, self.state, str(r_state), *sa_options).grid(row=5, column=1, padx=5, pady=10)

        # ERRORS
        self.te_label = ttk.Label(self.w_frame, text=self.t_ERROR, style='error.TLabel')
        self.te_label.grid(row=3, column=1, padx=5, sticky='w')

    def update_tab(self):
        """Updates widgets on write_tab function"""
        global assignment
        self.te_label.configure(text=self.t_ERROR)

    def submit(self):
        """Submitting User's Input and Appending it to the Database"""
        global SQL
        self.task.set(check_for_shortcuts(self.task.get()))
        # Checking Subject Entry
        if str(self.task.get()) == '':
            self.t_ERROR = 'Enter Task Name'
            self.update_tab()
            proceed1 = False
        else:
            proceed1 = True
            self.t_ERROR = ' '
        self.date.set(self.date_c.get())
        if proceed1:
            if self.update:
                if self.group == 'N/A':
                    self.group = '.'.join([str(self.id), '0'])
                    SQL.modify_task_group(self.group, self.id)
                else:
                    self.group = '.'.join([assignment[self.id].group, '0'])
                    SQL.modify_task_group(self.group, self.id)
            # If both are okay, appends task to memory
            if self.group == 'N/A':
                SQL.append_task(self.subject.get(), self.task.get(), self.date.get(),
                                main_state_list[self.state.get()], 'N/A', '', '')
            else:
                self.group = self.group.split('.')
                self.group.pop(-1)
                self.group = '.'.join(self.group)
                task = SQL.get_specific_task_data(4, '.'.join([self.group, '0']))
                task = assignment[task[0][-1]]
                self.group = '.'.join([self.group, str(len(task.tasks) + 1)])
                SQL.append_task(self.subject.get(), self.task.get(), self.date.get(),
                                main_state_list[self.state.get()], self.group, '', '')
                tasks_initialization()
                task = SQL.get_task_data()
                task = task[-1]
                task = Task(task[0], task[1], task[2], task[3], task[4], task[5], task[6], task[-1])
                tasks_initialization()
                menu.tab[1].update_treeview(task)
            menu.send_all_back()
            messagebox.showinfo("Assignment Manager Admin", "Task Appended!")
            menu.send_all_forward()
            self.destroy_window()
            window.pg1.update_treeview()

    def update(self):
        pass

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg1.enable_buttons()
            window.enable_notebook()
        else:
            self.root.destroy()
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
        menu.tabs -= 1


class Tk_Sub_Task:
    """Functions in task menu"""

    def __init__(self, master, task_id):
        self.root = master
        self.task_id = task_id
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()

        # TITLE
        ttk.Label(self.frame, text=f'Task Menu for {assignment[task_id].name}', style='sub_heading.TLabel') \
            .grid(row=0, column=0, columnspan=3, padx=20, pady=5)

        # Notebook
        self.nb = ttk.Notebook(self.frame, style='TNotebook')
        self.page1 = ttk.Frame(self.nb, style='main.TFrame')
        self.page2 = ttk.Frame(self.nb, style='main.TFrame')
        self.page3 = ttk.Frame(self.nb, style='main.TFrame')
        self.page4 = ttk.Frame(self.nb, style='main.TFrame')

        self.nb.grid(row=1, column=0, columnspan=3, sticky='news', pady=2)
        self.nb.add(self.page1, text='Modify Task')
        self.nb.add(self.page2, text='Sub Tasks')
        self.nb.add(self.page3, text='Repeats')
        self.nb.add(self.page4, text='Description')

        # Variables Init
        self.subject = tk.StringVar(self.root, value=assignment[task_id].subject)
        self.task = tk.StringVar(self.root, value=assignment[task_id].name)
        self.date = datetime.datetime.strptime(assignment[task_id].date, '%d/%m/%Y')
        self.state = tk.StringVar(self.root, value=all_state_list[assignment[task_id].state])
        self.occurrence = assignment[task_id].occurrence
        self.occurrence_times = tk.IntVar(self.root, value=assignment[task_id].occurrence_times)
        self.occurrence_type = tk.StringVar(self.root, value=assignment[task_id].occurrence_type)
        self.occurrence_days = assignment[task_id].occurrence_days
        self.occurrences = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 't': 'Thursday', 'F': 'Friday',
                            'S': 'Saturday', 's': 'Sunday'}
        self.occurrence_ran = False
        self.description = None
        self.date_c = None
        self.te_label = None
        self.t_ERROR = ''

        self.tree = None

        # Occurrence Menu Variables
        self.frame_o = None
        self.o_mode = tk.IntVar()
        if self.occurrence == '':
            self.o_mode.set(1)
        else:
            self.o_mode.set(2)
        self.frame_oo = None
        self.check_variables = {}

        # Init All
        self.task_modify_menu()
        self.sub_task_menu()
        self.occurrence_main_menu()
        self.description_menu()

        # Init Buttons (Delete, Apply, Exit)
        self.del_button = ttk.Button(self.frame, text='Delete', command=self.delete, style='main.TButton')
        self.del_button.grid(row=2, column=0, padx=2, sticky='news')
        self.apply_button = ttk.Button(self.frame, text='Apply', command=self.apply, style='main.TButton')
        self.apply_button.grid(row=2, column=1, padx=2, sticky='news')
        self.ext = ttk.Button(self.frame, text='Exit', command=self.destroy_window, style='main.TButton')
        self.ext.grid(row=2, column=2, padx=2, sticky='news')

        self.root.bind('<Control-Key-d>', lambda e: self.delete())
        self.root.bind('<Control-Key-a>', lambda e: self.apply())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def task_modify_menu(self):
        """Writes the task modify menu"""
        global Now
        Now = Timetable()
        Now.Now_Subject()

        self.page1.rowconfigure(0, weight=1)
        self.page1.columnconfigure(0, weight=1)
        frame_m = ttk.LabelFrame(self.page1, text='Modify Task:', style='main.TLabelframe')
        frame_m.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='news')

        frame_m.rowconfigure(0, weight=1)
        frame_m.rowconfigure(1, weight=1)
        frame_m.rowconfigure(3, weight=1)
        frame_m.rowconfigure(4, weight=1)
        frame_m.columnconfigure(0, weight=1)
        frame_m.columnconfigure(1, weight=3)

        ttk.Label(frame_m, text="Subject:", style='text.TLabel').grid(row=0, column=0, padx=5, pady=10)
        s_set = {Now.line1, Now.line2, Now.line3, Now.line4, Now.line5, Now.line6, Now.line7, Now.line8, Now.line9}
        s_options = []
        for i in s_set:
            s_options.append(i)
        sorting_items(Important)
        s_options = sorted(s_options, key=lambda x: subject_sort[x])
        ttk.OptionMenu(frame_m, self.subject, self.subject.get(), *s_options) \
            .grid(row=0, column=1, padx=5, pady=10, columnspan=2)

        # TASK LABEL AND ENTRY
        ttk.Label(frame_m, text="Name:", style='text.TLabel').grid(row=1, column=0, padx=5, pady=1)
        tk.Entry(frame_m, textvariable=self.task, font=('Helvetica', 12)).grid(row=1, column=1, padx=5, pady=1,
                                                                               sticky='ew')

        # DATE LABEL AND ENTRY
        ttk.Label(frame_m, text="Date:", style='text.TLabel').grid(row=3, column=0, padx=5, pady=5)
        self.date_c = DateEntry(frame_m, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                year=self.date.year, month=self.date.month, day=self.date.day,
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                                )
        self.date_c.grid(row=3, column=1, padx=5, pady=5)

        # STATE LABEL AND OptionMenu
        ttk.Label(frame_m, text="State:", style='text.TLabel').grid(row=4, column=0, padx=5, pady=10)
        if 'Completed' in self.state.get():
            ttk.Label(frame_m, text=self.state.get(), style='text.TLabel').grid(row=4, column=1, padx=5, pady=10)
        else:
            sa_options = []
            for states in range(0, int(len(main_state_list) / 2)):
                sa_options.append(main_state_list[states + 1])
            ttk.OptionMenu(frame_m, self.state, self.state.get(), *sa_options).grid(row=4, column=1, padx=5, pady=10)

        self.te_label = ttk.Label(frame_m, text=self.t_ERROR, style='error.TLabel')
        self.te_label.grid(row=2, column=1, padx=5, sticky='w')

    def update_tab(self):
        """Updates Modify Menu For User's Input Errors"""
        self.te_label.configure(text=self.t_ERROR)

    def sub_task_menu(self):
        """Initializes Sub Task Menu"""

        frame_m = ttk.LabelFrame(self.page2, text='Sub Tasks:', style='main.TLabelframe')
        frame_m.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        ttk.Button(frame_m, text='Move Task Up', command=self.move_up, style='main.TButton') \
            .grid(row=1, column=0, padx=2, pady=5)
        ttk.Button(frame_m, text='Move Task Down', command=self.move_down, style='main.TButton') \
            .grid(row=1, column=1, padx=2, pady=5)
        ttk.Button(frame_m, text='Add New Task', command=self.new_task, style='main.TButton') \
            .grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        tree_frame = ttk.Frame(frame_m, relief='flat', width=750, style='main.TFrame')
        tree_frame.grid(row=0, column=0, columnspan=2, sticky='NSEW', pady=5)
        x_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        y_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set, height=5)
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        self.tree['columns'] = ('Task', 'Due Date', 'Category', 'Reminders')

        # Format Columns
        self.tree.column('#0', width=100, minwidth=90, stretch=True)
        self.tree.column('Task', anchor='w', width=150, minwidth=100, stretch=True)
        self.tree.column('Due Date', anchor='w', width=90, minwidth=80, stretch=True)
        self.tree.column('Category', anchor='w', width=60, minwidth=30, stretch=True)
        self.tree.column('Reminders', anchor='w', width=100, minwidth=90, stretch=True)

        # Headings
        self.tree.heading('#0', text='Category/Subject', anchor='w')
        self.tree.heading('Task', text='Task Name', anchor='w')
        self.tree.heading('Due Date', text='Due Date', anchor='w')
        self.tree.heading('Category', text='Category', anchor='w')
        self.tree.heading('Reminders', text='Reminders', anchor='w')

        # Show Scrollbar
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.pack(side='right', fill='y')

        # Show Treeview
        self.tree.pack()

        index = 1
        for row in range(0, len(assignment[self.task_id].tasks)):
            task = assignment[self.task_id].tasks[row]
            iid = task.id
            state = all_state_list[task.state]
            self.tree.insert(parent='', index=index, iid=str(iid), text=task.subject,
                             values=(task.name, task.date, state, task.reminder))
            index += 1

    def move_up(self):
        """Moves selected task Up 1"""
        tasks = self.tree.selection()
        for task in tasks:
            self.tree.move(task, self.tree.parent(task), self.tree.index(task) - 1)

    def move_down(self):
        """Moves selected task Down 1"""
        tasks = self.tree.selection()
        for task in reversed(tasks):
            self.tree.move(task, self.tree.parent(task), self.tree.index(task) + 1)

    def update_treeview(self, task):
        """Updates Treeview"""
        index = task.group.split('.')
        state = all_state_list[task.state]
        self.tree.insert(parent='', index=index[-1], iid=str(task.id), text=task.subject,
                         values=(task.name, task.date, state, task.reminder))

    def new_task(self):
        """New Task Menu For User's Input Under This Task"""
        if assignment[self.task_id].group == 'N/A' or not assignment[self.task_id].main_task:
            Tk_Sub_NTask(tk.Toplevel(), assignment[self.task_id].group, True, self.task_id)
        else:
            Tk_Sub_NTask(tk.Toplevel(), assignment[self.task_id].group, False, self.task_id)

    def occurrence_main_menu(self):
        """Initializes Repeats Menu"""
        self.page3.rowconfigure(0, weight=1)
        self.page3.columnconfigure(0, weight=1)
        self.frame_o = ttk.LabelFrame(self.page3, text='Repeats:', style='main.TLabelframe')
        self.frame_o.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        self.frame_o.rowconfigure(0, weight=1)
        self.frame_o.rowconfigure(1, weight=3)
        self.frame_o.columnconfigure(0, weight=1)
        self.frame_o.columnconfigure(1, weight=1)

        ttk.Radiobutton(self.frame_o, text='No Repeats', variable=self.o_mode, value=1, command=self.no_occurrence) \
            .grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(self.frame_o, text='Add/Edit Repeats', variable=self.o_mode, value=2,
                        command=self.run_occurrence_menu).grid(row=0, column=1, padx=5, pady=5)
        if self.o_mode.get() == 2:
            self.occurrence_menu()
        else:
            self.occurrence_menu()
            self.no_occurrence()

    def no_occurrence(self):
        """Destroys Occurrences and Widgets"""
        try:
            self.occurrence = 'N/A'
            self.frame_oo.destroy()
            self.occurrence_ran = False
        except AttributeError:
            pass

    def run_occurrence_menu(self):
        if not self.occurrence_ran:
            self.occurrence_menu()
        self.occurrence_ran = True

    def occurrence_menu(self):
        """Initializes the Main Occurrence Menu, all different widgets if user's wants it"""
        self.occurrence = assignment[self.task_id].occurrence

        self.frame_oo = ttk.LabelFrame(self.frame_o, text='Repeats Menu', style='main.TLabelframe')
        self.frame_oo.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        self.frame_oo.columnconfigure(0, weight=1)
        self.frame_oo.columnconfigure(1, weight=1)
        self.frame_oo.columnconfigure(2, weight=1)
        self.frame_oo.columnconfigure(3, weight=6)

        ttk.Label(self.frame_oo, text='Repeat Every', style='text.TLabel').grid(row=0, column=0, padx=2, pady=10)

        if self.occurrence_times.get() < 0:
            self.occurrence_times.set(1)
        ttk.Spinbox(self.frame_oo, from_=0, to=99, textvariable=self.occurrence_times, width=2) \
            .grid(row=0, column=1, pady=10, sticky='w')

        occurrence_dict = {'': 'Days', 'D': 'Days', 'W': 'Weeks', 'M': 'Months', 'Y': 'Years',
                           'Days': 'Days', 'Weeks': 'Weeks', 'Months': 'Months', 'Years': 'Years'}
        occurrence_options = ['Days', 'Weeks', 'Months', 'Years']
        self.occurrence_type.set(occurrence_dict[self.occurrence_type.get()])
        ttk.OptionMenu(self.frame_oo, self.occurrence_type, self.occurrence_type.get(), *occurrence_options,
                       command=self.update_checkboxes).grid(row=0, column=2, padx=3, pady=10, sticky='w')

        # Specify Date Checkboxes
        frame_m = ttk.Frame(self.frame_oo, style='main.TFrame')
        frame_m.grid(row=1, column=0, columnspan=4, padx=4)

        frame_m.rowconfigure(0, weight=2)
        frame_m.rowconfigure(1, weight=1)
        frame_m.rowconfigure(2, weight=1)

        ttk.Label(frame_m, text='on the following days:', style='text.TLabel') \
            .grid(row=0, column=0, columnspan=5, padx=3, pady=5, sticky='w')

        # placement dict: {Day: [row, column]}
        placement = {'M': [1, 0], 'T': [1, 1], 'W': [1, 2], 't': [1, 3], 'F': [1, 4], 'S': [2, 1], 's': [2, 3]}
        for row in self.occurrences:
            # check_variables = {Day: [Checkbutton Widget, Checkbutton Variable]}
            self.check_variables[row] = ['', tk.BooleanVar()]
            if row in self.occurrence_days:
                self.check_variables[row][1].set(True)
            self.check_variables[row][0] = \
                ttk.Checkbutton(frame_m, text=self.occurrences[row], variable=self.check_variables[row][1])
            self.check_variables[row][0].grid(
                row=placement[row][0], column=placement[row][1], padx=10, pady=5, sticky='w')

        # Update the checkboxes according to original settings
        self.update_checkboxes(self.occurrence_type.get())

    def update_checkboxes(self, choice):
        """Updates checkboxes on occurrence menu"""
        self.occurrence_days = []
        for row in self.occurrences:
            if self.check_variables[row][1].get():
                self.occurrence_days.append(row)
        if choice == 'Days':
            for row in self.occurrences:
                self.check_variables[row][0]['state'] = 'disabled'
                if self.check_variables[row][1].get():
                    self.occurrence_days.append(row)
                self.check_variables[row][1].set(False)
        else:
            for row in self.occurrences:
                self.check_variables[row][0]['state'] = 'normal'
                if row in self.occurrence_days:
                    self.check_variables[row][1].set(True)

    def description_menu(self):
        """Initializes Description Menu"""
        self.page4.rowconfigure(0, weight=1)
        self.page4.columnconfigure(0, weight=1)
        frame_m = ttk.LabelFrame(self.page4, text='Description/Notes:', padding=2, style='main.TLabelframe')
        frame_m.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        x_scroll = ttk.Scrollbar(frame_m, orient='horizontal')
        y_scroll = ttk.Scrollbar(frame_m, orient='vertical')

        self.description = tk.Text(frame_m, width=55, height=12, font=('Helvetica', 12),
                                   xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set, wrap='none')
        self.description.insert(tk.END, assignment[self.task_id].description)
        self.description.delete('end-1c', tk.END)

        x_scroll.config(command=self.description.xview)
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.config(command=self.description.yview)
        y_scroll.pack(side='right', fill='y')
        self.description.pack()

    def delete(self):
        """Deletes this Task"""
        SQL.modify_task_groups(assignment[self.task_id])
        tasks_initialization()
        window.pg1.update_treeview()
        self.destroy_window()

    def apply(self):
        """Applying all Edits from the User and puts it into the database"""
        self.task.set(check_for_shortcuts(self.task.get()))
        if str(self.task.get()) == '':
            self.t_ERROR = 'Enter Task Name'
            self.update_tab()
            proceed1 = False
        else:
            proceed1 = True
            self.t_ERROR = ' '
            self.update_tab()
        self.date = self.date_c.get()
        if proceed1:
            state = all_state_list[self.state.get()]
            self.occurrence_days = []
            for row in self.occurrences:
                if self.check_variables[row][1].get():
                    self.occurrence_days.append(row)
            occurrence_dict = {'Days': 'D', 'Weeks': 'W', 'Months': 'M', 'Years': 'Y'}
            self.occurrence_type.set(occurrence_dict[self.occurrence_type.get()])
            if self.occurrence == 'N/A':
                self.occurrence = ''
            else:
                try:
                    self.occurrence_times.get()
                except tkinter.TclError:
                    self.occurrence_times.set(1)
                self.occurrence = \
                    [str(self.occurrence_times.get()), self.occurrence_type.get(), ''.join(self.occurrence_days)]
            task = Task(self.subject.get(), self.task.get(), self.date,
                        state, assignment[self.task_id].group, ' '.join(self.occurrence),
                        self.description.get(1.0, tk.END), self.task_id)
            SQL.modify_task(task, self.task_id)
            for row in self.tree.get_children():
                row = int(row)
                SQL.modify_task_group('.'.join([assignment[row].main_group, str(self.tree.index(row) + 1)]), row)
            window.pg1.update_treeview()

            occurrence_dict = {'': 'Days', 'D': 'Days', 'W': 'Weeks', 'M': 'Months', 'Y': 'Years',
                               'Days': 'Days', 'Weeks': 'Weeks', 'Months': 'Months', 'Years': 'Years'}
            self.occurrence_type.set(occurrence_dict[self.occurrence_type.get()])

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg1.enable_buttons()
            window.enable_notebook()
        else:
            self.root.destroy()
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
        menu.tabs -= 1


class Tk_Sub_Subject:
    """Functions in subject menu"""

    def __init__(self, master, subject_info):
        """Initialize Sub Menu For Subjects"""
        self.root = master
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.s_row = subject_info[0]
        self.s_column = subject_info[1]
        occurrence_dict = {1: 'M', 2: 'T', 3: 'W', 4: 't', 5: 'F'}
        line = SQL.get_occurrence_subject_data(occurrence_dict[self.s_row] + str(self.s_column))
        self.subject = Subject(line[0][0], line[0][1], line[0][2], line[0][3],
                               line[0][4])
        self.name = tk.StringVar(self.root, value=self.subject.name)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()
        ttk.Label(self.frame, text=f'SUBJECT MENU FOR {self.subject.name}', style='sub_heading.TLabel') \
            .grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky='w')

        self.items = self.subject.items
        self.new_item = tk.StringVar()
        self.item_row = {}
        self.items_row = 0
        self.error_label = ttk.Label()
        self.items_frame = None
        self.no_item = None
        self.canvas = None

        # Notebook
        self.nb = ttk.Notebook(self.frame, style='TNotebook')
        self.page1 = ttk.Frame(self.nb, style='main.TFrame')
        self.page2 = ttk.Frame(self.nb, style='main.TFrame')
        self.page3 = ttk.Frame(self.nb, style='main.TFrame')

        self.nb.grid(row=1, column=0, columnspan=2, sticky='news', pady=2)
        self.nb.add(self.page1, text='Modify Subject/Items List')
        self.nb.add(self.page2, text='Tasks')
        self.nb.add(self.page3, text='Description')

        self.a_button = ttk.Button(self.frame, text='Apply', command=self.apply, padding=2, style='main.TButton')
        self.a_button.grid(row=2, column=0, padx=1, pady=5, sticky='news')
        self.c_button = ttk.Button(self.frame, text='Cancel', command=self.destroy_window, padding=2,
                                   style='main.TButton')
        self.c_button.grid(row=2, column=1, padx=1, pady=5, sticky='news')
        self.t_button = None
        self.description = None

        self.subject_mod_menu()
        self.view_tasks_menu()
        self.items_menu()
        self.description_menu()
        self.root.bind('<Control-Key-a>', lambda e: self.apply())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def subject_mod_menu(self):
        """Setup Modify Subject Frame and Widgets"""
        self.page1.rowconfigure(0, weight=1)
        self.page1.columnconfigure(0, weight=1)
        self.page1.columnconfigure(1, weight=1)
        frame = ttk.LabelFrame(self.page1, text='Modify Subject Details: ', padding=2, style='main.TLabelframe')
        frame.grid(row=0, column=0, padx=1, pady=5, sticky='news')
        frame.rowconfigure(0, weight=2)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text='Subject: ', style='text.TLabel').grid(row=0, column=0, padx=3, pady=5)
        tk.Entry(frame, textvariable=self.name).grid(row=0, column=1, padx=3, pady=5, sticky='ew')

        self.t_button = ttk.Button(frame, text='Modify Timetable Pattern', command=self.show_mod_timetable,
                                   style='main.TButton')
        self.t_button.grid(row=1, column=0, padx=8, pady=7, columnspan=2)

    def view_tasks_menu(self):
        self.page2.rowconfigure(0, weight=1)
        self.page2.columnconfigure(0, weight=1)
        frame = ttk.LabelFrame(self.page2, text=f'All Tasks Under {self.subject.name}: ', padding=2,
                               style='main.TLabelframe')
        frame.grid(row=0, column=0, padx=1, pady=5, sticky='news')

        tree_frame = ttk.Frame(frame, relief='flat', width=750, style='main.TFrame')
        tree_frame.grid(row=0, column=0, columnspan=2, sticky='NSEW', pady=5)
        x_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        y_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        tree = ttk.Treeview(tree_frame, yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set, height=5)
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)

        tree['columns'] = ('Task', 'Due Date', 'Category', 'Reminders')

        # Format Columns
        tree.column('#0', width=100, minwidth=90, stretch=True)
        tree.column('Task', anchor='w', width=150, minwidth=100, stretch=True)
        tree.column('Due Date', anchor='w', width=90, minwidth=80, stretch=True)
        tree.column('Category', anchor='w', width=60, minwidth=30, stretch=True)
        tree.column('Reminders', anchor='w', width=100, minwidth=90, stretch=True)

        # Headings
        tree.heading('#0', text='Category/Subject', anchor='w')
        tree.heading('Task', text='Task Name', anchor='w')
        tree.heading('Due Date', text='Due Date', anchor='w')
        tree.heading('Category', text='Category', anchor='w')
        tree.heading('Reminders', text='Reminders', anchor='w')

        # Show Scrollbar
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.pack(side='right', fill='y')

        # Show Treeview
        tree.pack()

        index = 0
        for row in range(0, len(self.subject.tasks)):
            iid = self.subject.tasks[row].id
            state = all_state_list[self.subject.tasks[row].state]
            tree.insert(parent='', index=index, iid=str(iid), text=self.subject.tasks[row].subject,
                        values=(self.subject.tasks[row].name, self.subject.tasks[row].date,
                                state, self.subject.tasks[row].reminder))
            index += 1

    def items_menu(self):
        frame = ttk.LabelFrame(self.page1, text='Items List For This Lesson:', padding=2, style='main.TLabelframe')
        frame.grid(row=0, column=1, padx=1, pady=5, sticky='news')
        frame.rowconfigure(0, weight=7)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=7)
        frame.columnconfigure(1, weight=1)

        frame1 = ttk.Frame(frame, style='main.TFrame')
        frame1.grid(row=0, column=0, columnspan=2, padx=2, pady=3)

        self.canvas = tk.Canvas(frame1, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                                height=90, width=220, highlightthickness=0)
        self.canvas.pack(side='left', fill=tk.BOTH, expand=1)

        scroll = ttk.Scrollbar(frame1, orient='vertical', command=self.canvas.yview)
        scroll.pack(side='right', fill='y')

        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.items_frame = ttk.Frame(self.canvas, style='main.TFrame')
        self.canvas.create_window((0, 0), window=self.items_frame, anchor='nw')

        self.items_frame.columnconfigure(0, weight=1)
        for item in self.items:
            self.item_row[item] = [self.items_row, None]
            self.item_row[item][1] = ttk.Button(self.items_frame, text=f' -  {item}',
                                                command=lambda x=item: self.delete_item(x), style='list.TButton')
            self.item_row[item][1].grid(row=self.item_row[item][0], column=0, padx=3, pady=2)
            self.items_row += 1
        if len(self.items) == 0:
            self.no_item = ttk.Label(self.items_frame, text='None', style='sub_heading.TLabel')
            self.no_item.grid(row=0, column=0, padx=3, pady=2, sticky='ew')

        entry = ttk.Entry(frame, textvariable=self.new_item, width=30)
        entry.grid(row=1, column=0, pady=5, sticky='ew')
        entry.bind('<Return>', lambda e: self.add_item())
        ttk.Button(frame, text='Add', command=self.add_item, width=5, style='main.TButton') \
            .grid(row=1, column=1, padx=3, pady=5)
        self.error_label = ttk.Label(frame, text='', style='error.TLabel')
        self.error_label.grid(row=2, column=0, columnspan=2, pady=1, sticky='w')
        ttk.Label(frame, text='Click Item To Delete', style='text.TLabel') \
            .grid(row=3, column=0, columnspan=2, padx=3, pady=5, sticky='ew')

    def add_item(self):
        """Adds a new item to the items list"""
        item = self.new_item.get()
        if item in self.items or item == '':
            self.error_label.configure(text='Item already exists or invalid item name entered')
        else:
            try:
                self.no_item.destroy()
            except AttributeError:
                pass
            self.error_label.configure(text='')
            self.items_row += 1
            self.item_row[item] = [self.items_row, None]
            self.item_row[item][1] = ttk.Button(self.items_frame, text=f' -  {item}',
                                                command=lambda x=item: self.delete_item(x), style='list.TButton')
            self.item_row[item][1].grid(row=self.item_row[item][0], column=0, padx=3, pady=2, sticky='ew')
            self.items.append(item)
            self.new_item.set('')
            self.update_canvas()

    def update_canvas(self):
        """Updates Canvas Scrollbar"""
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def delete_item(self, item):
        """Deletes selected item"""
        self.item_row[item][1].destroy()
        del self.item_row[item]
        if len(self.item_row) == 0:
            self.no_item = ttk.Label(self.items_frame, text='None', style='sub_heading.TLabel')
            self.no_item.grid(row=0, column=0, padx=3, pady=2, sticky='ew')
        self.items.remove(item)
        self.update_canvas()

    def description_menu(self):
        """Initializes the Description Menu"""
        self.page3.rowconfigure(0, weight=1)
        self.page3.columnconfigure(0, weight=1)
        frame = ttk.LabelFrame(self.page3, text='Description/Notes:', padding=2, style='main.TLabelframe')
        frame.grid(row=0, column=0, padx=5, pady=5, sticky='NEWS')

        x_scroll = ttk.Scrollbar(frame, orient='horizontal')
        y_scroll = ttk.Scrollbar(frame, orient='vertical')
        self.description = tk.Text(frame, width=54, height=10, font=('Helvetica', 12),
                                   xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set, wrap='none')
        self.description.insert(tk.END, self.subject.description)
        self.description.delete('end-1c', tk.END)

        x_scroll.config(command=self.description.xview)
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.config(command=self.description.yview)
        y_scroll.pack(side='right', fill='y')
        self.description.pack()

    def apply(self):
        """Apply Button Functions"""
        SQL.modify_subject(self.subject.line, self.name.get())
        SQL.modify_subject_details(self.subject.line, ','.join(self.subject.items),
                                   self.description.get(1.0, tk.END))
        window.pg2.update_timetable()

    def show_mod_timetable(self):
        """Shows the Line Modification Timetable Window"""
        self.disable_buttons()
        menu.timetable_window()

    def disable_buttons(self):
        """Disables buttons to prevent multiple menu tabs"""
        self.a_button['state'] = 'disabled'
        self.c_button['state'] = 'disabled'
        self.t_button['state'] = 'disabled'

    def enable_buttons(self):
        """Enables buttons from their disabled state"""
        self.a_button['state'] = 'normal'
        self.c_button['state'] = 'normal'
        self.t_button['state'] = 'normal'

    def update(self):
        pass

    def destroy_window(self):
        """Destroys the window"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg2.enable_buttons()
            window.enable_notebook()
        else:
            self.root.destroy()
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
        menu.tabs -= 1


class Tk_Sub_Timetable:
    """Functions for timetable pattern modify menu"""

    def __init__(self, master):
        """Initialize Timetable Menu"""
        self.root = master
        self.row_dict = {1: 'M', 2: 'T', 3: 'W', 4: 't', 5: 'F'}
        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()

        self.timetable_frame = ttk.Frame(self.frame, relief='flat', style='main.TFrame')
        self.timetable_frame.grid(row=1, column=0)
        self.button_n = {}
        self.subject = {}
        self.days = range(1, 5 + 1)
        self.periods = range(1, len(Now.period_dict))
        self.show_modify_timetable()
        ttk.Button(self.frame, text='Apply', command=self.apply, style='main.TButton') \
            .grid(row=2, column=0, columnspan=2, padx=30)

        self.root.bind('<Control-Key-a>', lambda e: self.apply())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def show_modify_timetable(self):
        """Writes all widgets for modify timetable"""
        # TITLE
        frame_t = ttk.Frame(self.timetable_frame, relief='solid', style='main.TFrame')
        frame_t.grid(row=0, column=0, sticky='news')
        ttk.Label(frame_t, text='TIMETABLE', style='Timetable.TLabel').grid(row=0, column=0, padx=3, pady=4)

        # X TITLE FRAMES AND LABELS
        table_x_title = {}
        day_dict = {1: 'MONDAY', 2: 'TUESDAY', 3: 'WEDNESDAY', 4: 'THURSDAY', 5: 'FRIDAY'}
        for day in self.days:
            table_x_title[day] = ttk.Frame(self.timetable_frame, relief='solid', style='main.TFrame')
            table_x_title[day].grid(row=0, column=day, sticky='news')
            ttk.Label(table_x_title[day], text='{: ^11}'.format(day_dict[day]), style='Timetable.TLabel') \
                .grid(row=0, column=0, padx=3, pady=4)

        # TIME FRAMES AND LABELS
        table_y_title = {}
        for period in self.periods:
            table_y_title[period] = ttk.Frame(self.timetable_frame, relief='groove', style='main.TFrame')
            table_y_title[period].grid(row=period, column=0, sticky='news')
            ttk.Label(table_y_title[period], text='{: ^9}\n{: >6}\n{: ^9}'
                      .format(Now.period_dict[period], '-', Now.period_dict[period + 1]),
                      style='Timetable_side.TLabel').grid(row=0, column=0, padx=30, pady=4)

        # SUBJECTS
        table_contents = {}
        for day in self.days:
            table_contents[day] = {}
            self.button_n[day] = {}
            self.subject[day] = {}
            for period in self.periods:
                table_contents[day][period] = ttk.Frame(self.timetable_frame, relief='groove', style='main.TFrame')
                table_contents[day][period].grid(row=period, column=day, sticky='news')

                self.subject[day][period] = Subject(self.check_for_occurrence([day, period], 0),
                                                    self.check_for_occurrence([day, period], 1),
                                                    self.check_for_occurrence([day, period], 2),
                                                    self.check_for_occurrence([day, period], 3),
                                                    self.check_for_occurrence([day, period], 4))
                self.button_n[day][period] = \
                    ttk.Button(table_contents[day][period], text=f'line {self.subject[day][period].line}',
                               command=lambda x=day, y=period: self.change_line(x, y, self.subject[x][y].line),
                               style='main.TButton')
                self.button_n[day][period].grid(row=0, column=0, sticky='news')

    def check_for_occurrence(self, occurrence: list, item: int):
        """Check if 'occurrence' exists in data sets"""
        occurrence[0] = self.row_dict[occurrence[0]]
        data = SQL.get_occurrence_subject_data(''.join([str(occurrence[0]), str(occurrence[1])]))
        if not data:
            line_n = 1
        else:
            line_n = data[0][item]
        return line_n

    def change_line(self, day, period, line_n):
        """Changes the line and text for buttons"""
        length = len(Now.line_dict) - 1
        if line_n <= length:
            self.button_n[day][period].configure(text='line ' + str(line_n + 1))
            self.subject[day][period].line += 1
        else:
            self.button_n[day][period].configure(text='line ' + str(line_n - length))
            self.subject[day][period].line -= length

    def apply(self):
        """Apply Button Functions"""
        occurrence_dict = {1: 'M', 2: 'T', 3: 'W', 4: 't', 5: 'F'}
        for i in self.days:
            for j in self.periods:
                line = self.subject[i][j].line
                SQL.modify_occurrence(line, '')
        for i in self.days:
            x = occurrence_dict[i]
            for j in self.periods:
                line = self.subject[i][j].line
                data = SQL.get_line_subject_data(line)[0][2]
                occurrence = ''.join([data, ' ', x + str(j)])
                if not x + str(j) in data:
                    SQL.modify_occurrence(line, occurrence)
        self.destroy_window()

    def update(self):
        pass

    def destroy_window(self):
        """Destroys the window"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg2.enable_buttons()
            window.enable_notebook()
        else:
            self.root.destroy()
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
        menu.tabs -= 1


class Tk_Sub_NEvent:
    """Functions in write new event menu"""

    def __init__(self, master, orig_id, date=datetime.date.today()):
        """Initializes a new event menu"""
        global assignment
        self.root = master
        self.orig_id = orig_id
        try:
            date = datetime.datetime.strptime(str(date), '%m/%d/%y')
        except ValueError:
            date = datetime.datetime.strptime(str(date), '%d/%m/%Y')
        self.date = date
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()
        self.w_frame = ttk.Frame(self.frame, relief='raised', padding=10, style='main.TFrame')
        self.w_frame.grid(row=1, column=0, columnspan=2, sticky='news')

        # TITLE
        if self.orig_id != 'N/A':
            title = ' for ' + assignment[self.orig_id].name
        else:
            title = ''
        ttk.Label(self.frame, text=f'Write New Event{title}', style='sub_heading.TLabel') \
            .grid(row=0, column=0, columnspan=2, padx=20, pady=5)

        self.name = tk.StringVar()
        self.s_date_h = tk.IntVar()
        self.s_date_m = tk.IntVar()
        self.e_date_h = tk.IntVar()
        self.e_date_m = tk.IntVar()
        self.col = [0, '#0013ff']
        self.date_s = None
        self.date_e = None
        self.te_label = None
        self.t_ERROR = ''
        self.write_menu()

        ttk.Button(self.frame, text="Submit", command=self.submit, style='main.TButton') \
            .grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        ttk.Button(self.frame, text="Cancel", command=self.destroy_window, style='main.TButton') \
            .grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        self.root.bind('<Return>', lambda e: self.submit())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def write_menu(self):
        """Initializes Writing Menu For a New Event"""
        ttk.Label(self.w_frame, text='Name:', style='text.TLabel').grid(row=1, column=0, padx=5, pady=2)
        ttk.Entry(self.w_frame, textvariable=self.name, width=50).grid(row=1, column=1, padx=5, pady=2, columnspan=5)

        ttk.Label(self.w_frame, text="Start Date:", style='text.TLabel') \
            .grid(row=3, column=0, padx=5, pady=5, columnspan=2, sticky='w')
        self.date_s = DateEntry(self.w_frame, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                day=self.date.day, month=self.date.month, year=self.date.year,
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                                )
        self.date_s.grid(row=3, column=2, padx=5, pady=5, sticky='w')
        ttk.Spinbox(self.w_frame, from_=0, to=23, textvariable=self.s_date_h, width=2) \
            .grid(row=3, column=3, pady=5, sticky='e')
        ttk.Label(self.w_frame, text=':', style='text.TLabel').grid(row=3, column=4)
        ttk.Spinbox(self.w_frame, from_=0, to=60, textvariable=self.s_date_m, width=2) \
            .grid(row=3, column=5, pady=5, sticky='w')

        ttk.Label(self.w_frame, text="End Date:", style='text.TLabel') \
            .grid(row=4, column=0, padx=5, pady=1, columnspan=2, sticky='w')
        self.date_e = DateEntry(self.w_frame, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                day=self.date.day, month=self.date.month, year=self.date.year,
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                                )
        self.date_e.grid(row=4, column=2, padx=5, pady=5, sticky='w')
        ttk.Spinbox(self.w_frame, from_=0, to=23, textvariable=self.e_date_h, width=2) \
            .grid(row=4, column=3, pady=5, sticky='e')
        ttk.Label(self.w_frame, text=':', style='text.TLabel').grid(row=4, column=4)
        ttk.Spinbox(self.w_frame, from_=0, to=60, textvariable=self.e_date_m, width=2) \
            .grid(row=4, column=5, pady=5, sticky='w')

        def color_chooser():
            global menu
            orig_color = self.col
            menu.send_all_back()
            self.col = askcolor(color=orig_color[1], title="Choose a Color")
            menu.send_all_forward()
            if self.col[1] is not None:
                color = str(self.col[1])
                window.style.configure(f'{color}l.TButton', foreground=f'{lighter_col(color, 1)}',
                                       font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                window.style.map(f'{color}l.TButton', background=[('!active', f'{color}'),
                                                                  ('active', lighter_col(color, 1.1))])
                col_button.config(text=color, style=f'{color}l.TButton')
            else:
                self.col = orig_color

        # STATE LABEL AND OptionMenu
        ttk.Label(self.w_frame, text="Color:", style='text.TLabel').grid(row=5, column=0, padx=5, pady=10)
        window.style.configure(f'{self.col[1]}l.TButton', foreground=f'{lighter_col(self.col[1], 1)}',
                               font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
        window.style.map(f'{self.col[1]}l.TButton', background=[('!active', f'{self.col[1]}'),
                                                                ('active', lighter_col(self.col[1], 1.1))])
        col_button = ttk.Button(self.w_frame, text=self.col[1], style=f'{self.col[1]}l.TButton',
                                command=color_chooser)
        col_button.grid(row=5, column=1, columnspan=2, sticky='w')

        # ERRORS
        self.te_label = ttk.Label(self.w_frame, text=self.t_ERROR, style='error.TLabel')
        self.te_label.grid(row=2, column=1, padx=5, pady=1, sticky='w', columnspan=3)

    def submit(self):
        """Submitting User's Input and Appending it to the Database"""
        global SQL
        self.name.set(check_for_shortcuts(self.name.get()))
        proceed1 = True
        # Checking Subject Entry
        if self.name.get() == '':
            self.t_ERROR = 'Enter Event Name'
            self.te_label.configure(text=self.t_ERROR)
            proceed1 = False
        try:
            if not 0 <= self.s_date_h.get() <= 23 or not 0 <= self.e_date_h.get() <= 23:
                self.t_ERROR = 'Improper Time Detected'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
            elif not 0 <= self.s_date_m.get() <= 60 or not 0 <= self.e_date_m.get() <= 60:
                self.t_ERROR = 'Improper Time Detected'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
            elif datetime.datetime.strptime(f'{self.date_s.get()} {self.s_date_h.get()}:{self.s_date_m.get()}',
                                            '%d/%m/%Y %H:%M') > \
                    datetime.datetime.strptime(f'{self.date_e.get()} {self.e_date_h.get()}:{self.e_date_m.get()}',
                                               '%d/%m/%Y %H:%M'):
                self.t_ERROR = 'End Date & Time Must Be After Start Date & Time'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
        except tkinter.TclError:
            self.t_ERROR = 'Improper Time Detected'
            self.te_label.configure(text=self.t_ERROR)
            proceed1 = False

        if proceed1:
            self.t_ERROR = ''
            self.te_label.configure(text=self.t_ERROR)
            SQL.append_event(self.name.get(), f'{self.date_s.get()} {self.s_date_h.get()}:{self.s_date_m.get()}',
                             f'{self.date_e.get()} {self.e_date_h.get()}:{self.e_date_m.get()}',
                             self.orig_id, '', '', self.col[1])
            menu.send_all_back()
            messagebox.showinfo("Events Manager Admin", "Event Added!")
            menu.send_all_forward()
            self.destroy_window()
            events_initialization()
            window.Styles()

    def update(self):
        pass

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg3.enable_buttons()
            window.pg3.update()
            window.enable_notebook()
        else:
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
            self.root.destroy()
        menu.tabs -= 1


class Tk_Sub_Date:
    """Functions in date menu"""

    def __init__(self, master, date):
        """Initializes a date menu"""
        self.root = master
        self.buttons = []
        self.e_buttons = []
        try:
            date = datetime.datetime.strptime(str(date), '%m/%d/%y')
        except ValueError:
            date = datetime.datetime.strptime(str(date), '%d/%m/%Y')
        self.date = date

        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=8)
        self.frame.rowconfigure(2, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        ttk.Label(self.frame, text=f'Events on {self.date.day}/{self.date.month}/{self.date.year}',
                  style='sub_heading.TLabel').grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)
        self.buttons.append(ttk.Button(self.frame, text="+ New Event", style='main.TButton',
                                       command=self.new_event_menu))
        self.buttons[-1].grid(row=2, column=0, sticky='news', padx=2, pady=1)
        self.buttons.append(ttk.Button(self.frame, text='Exit', style='main.TButton', command=self.destroy_window))
        self.buttons[-1].grid(row=2, column=1, sticky='news', padx=2, pady=1)

        self.c_frame = ttk.Frame(self.frame, style='main.TFrame')
        self.events_tab()

        self.root.bind('<Control-Key-e>', lambda e: self.new_event_menu())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def events_tab(self):
        """Functions For Events Tab on Date"""
        self.c_frame.grid(row=1, column=0, columnspan=2, sticky='news', padx=2, pady=5)

        canvas1 = tk.Canvas(self.c_frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                            height=100, width=256, highlightthickness=0)

        y_scroll1 = ttk.Scrollbar(self.c_frame, orient='vertical', command=canvas1.yview)
        y_scroll1.grid(row=1, column=1, sticky='ns')

        canvas1.configure(yscrollcommand=y_scroll1.set)
        canvas1.grid(row=1, column=0, sticky='news')
        t_frame = ttk.Frame(canvas1, style='main.TFrame')
        canvas1.create_window((0, 0), window=t_frame, anchor='nw')
        t_frame.bind('<Configure>', lambda e: canvas1.configure(scrollregion=canvas1.bbox('all')))

        event = SQL.get_events_in_date(str(f'{self.date.day}/{self.date.month}/{self.date.year}'))
        for k in range(0, len(event)):
            n_event = event_[event[k][-1]]
            self.e_buttons.append(
                ttk.Button(t_frame, text=f'{n_event.name}\n{str(n_event.start_date.hour).zfill(2)}:'
                                         f'{str(n_event.start_date.minute).zfill(2)}\t'
                                         f'{str(n_event.start_date.day).zfill(2)}/'
                                         f'{str(n_event.start_date.month).zfill(2)}/'
                                         f'{n_event.start_date.year}        -\t'
                                         f'{str(n_event.end_date.hour).zfill(2)}:'
                                         f'{str(n_event.end_date.minute).zfill(2)}\t'
                                         f'{str(n_event.end_date.day).zfill(2)}/{str(n_event.end_date.month).zfill(2)}/'
                                         f'{n_event.end_date.year}',
                           style=f'{n_event.color}.TButton', command=lambda i=n_event.id: self.event_menu(i),
                           width=41))
            self.e_buttons[-1].grid(row=k, column=0, pady=2, sticky='w')

    def new_event_menu(self):
        """Shows the new event menu"""
        self.disable_buttons()
        menu.new_event_window('N/A', datetime.datetime.strftime(self.date, '%d/%m/%Y'))

    def event_menu(self, event_id: int):
        """Shows the event menu whenever an event button is pressed"""
        self.disable_buttons()
        menu.event_window(event_id)

    def update(self):
        """Updates Buttons"""
        self.c_frame.destroy()
        self.e_buttons = []
        self.c_frame = ttk.Frame(self.frame, style='main.TFrame')
        self.events_tab()

    def disable_buttons(self):
        """Disables all buttons"""
        for button in self.buttons:
            button['state'] = 'disabled'
        for button in self.e_buttons:
            button['state'] = 'disabled'

    def enable_buttons(self):
        """Enables all buttons"""
        for button in self.buttons:
            button['state'] = 'normal'
        for button in self.e_buttons:
            button['state'] = 'normal'

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg3.enable_buttons()
            window.pg3.update()
            window.enable_notebook()
        else:
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
            self.root.destroy()
        menu.tabs -= 1


class Tk_Sub_Event:
    """Functions in Event Menu"""

    def __init__(self, master, event_id: int):
        self.root = master
        self.event_id = event_id

        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()

        # TITLE
        ttk.Label(self.frame, text=f'Event Menu for {event_[event_id].name}', style='sub_heading.TLabel') \
            .grid(row=0, column=0, columnspan=3, padx=20, pady=5)

        # Notebook
        self.nb = ttk.Notebook(self.frame, style='TNotebook')
        self.page1 = ttk.Frame(self.nb, style='main.TFrame')
        self.page2 = ttk.Frame(self.nb, style='main.TFrame')
        self.page3 = ttk.Frame(self.nb, style='main.TFrame')

        self.nb.grid(row=1, column=0, columnspan=3, sticky='news', pady=2)
        self.nb.add(self.page1, text='Event Settings')
        self.nb.add(self.page2, text='Repeats')
        self.nb.add(self.page3, text='Description')

        self.name = tk.StringVar(self.root, value=event_[event_id].name)
        self.s_date = event_[event_id].start_date
        self.e_date = event_[event_id].end_date
        self.orig_id = event_[event_id].orig_id
        self.occurrence = event_[event_id].occurrence
        self.occurrence_times = tk.IntVar(self.root, value=event_[event_id].occurrence_times)
        self.occurrence_type = tk.StringVar(self.root, value=event_[event_id].occurrence_type)
        self.occurrence_days = event_[event_id].occurrence_days
        self.occurrences = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 't': 'Thursday', 'F': 'Friday',
                            'S': 'Saturday', 's': 'Sunday'}
        self.occurrence_ran = False
        self.description = event_[event_id].description
        self.col = event_[event_id].color

        self.date_s = None
        self.s_date_h = tk.IntVar(self.root, value=self.s_date.hour)
        self.s_date_m = tk.IntVar(self.root, value=self.s_date.minute)
        self.date_e = None
        self.e_date_h = tk.IntVar(self.root, value=self.e_date.hour)
        self.e_date_m = tk.IntVar(self.root, value=self.e_date.minute)

        self.t_ERROR = None
        self.te_label = None

        # Occurrence Menu Variables
        self.frame_o = None
        self.o_mode = tk.IntVar()
        if self.occurrence == '':
            self.o_mode.set(1)
        else:
            self.o_mode.set(2)
        self.frame_oo = None
        self.check_variables = {}

        self.settings_menu()
        self.occurrence_main_menu()
        self.description_menu()

        # Init Buttons (Delete, Apply, Exit)
        self.del_button = ttk.Button(self.frame, text='Delete', command=self.delete, style='main.TButton')
        self.del_button.grid(row=2, column=0, padx=2, sticky='news')
        self.apply_button = ttk.Button(self.frame, text='Apply', command=self.apply, style='main.TButton')
        self.apply_button.grid(row=2, column=1, padx=2, sticky='news')
        self.ext = ttk.Button(self.frame, text='Exit', command=self.destroy_window, style='main.TButton')
        self.ext.grid(row=2, column=2, padx=2, sticky='news')

        self.root.bind('<Control-Key-d>', lambda e: self.delete())
        self.root.bind('<Control-Key-a>', lambda e: self.apply())
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def settings_menu(self):
        """Initializes Settings Menu For an Event"""
        frame = ttk.Frame(self.page1, style='main.TFrame')
        frame.pack(expand=1, fill='both')
        frame.rowconfigure(0, weight=8)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=8)
        frame.rowconfigure(3, weight=8)
        frame.rowconfigure(4, weight=8)
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=5)
        frame.columnconfigure(3, weight=3)
        frame.columnconfigure(4, weight=1)
        frame.columnconfigure(5, weight=3)

        ttk.Label(frame, text='Name:', style='text.TLabel').grid(row=1, column=0, padx=5, pady=2)
        tk.Entry(frame, textvariable=self.name, font=('Helvetica', 12)).grid(row=1, column=1, padx=5, pady=2,
                                                                             columnspan=5, sticky='ew')

        ttk.Label(frame, text="Start Date:", style='text.TLabel') \
            .grid(row=3, column=0, padx=5, pady=5, columnspan=2, sticky='w')
        self.date_s = DateEntry(frame, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                day=self.s_date.day, month=self.s_date.month, year=self.s_date.year,
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                                )
        self.date_s.grid(row=3, column=2, padx=5, pady=5, sticky='w')
        ttk.Spinbox(frame, from_=0, to=23, textvariable=self.s_date_h, width=2) \
            .grid(row=3, column=3, pady=5, sticky='e')
        ttk.Label(frame, text=':', style='text.TLabel').grid(row=3, column=4)
        ttk.Spinbox(frame, from_=0, to=60, textvariable=self.s_date_m, width=2) \
            .grid(row=3, column=5, pady=5, sticky='w')

        ttk.Label(frame, text="End Date:", style='text.TLabel') \
            .grid(row=4, column=0, padx=5, pady=1, columnspan=2, sticky='w')
        self.date_e = DateEntry(frame, width=12, locale="en_AU", date_pattern='dd/mm/yyyy',
                                day=self.e_date.day, month=self.e_date.month, year=self.e_date.year,
                                background=SQL.get_cus_setting_values_for("Heading")[0][4],
                                foreground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][4], 1),
                                headersbackground=SQL.get_cus_setting_values_for("Heading")[0][3],
                                headersforeground=lighter_col(SQL.get_cus_setting_values_for("Heading")[0][3], 1),
                                normalbackground=SQL.get_cus_setting_values_for("Frame")[0][3],
                                normalforeground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1),
                                othermonthbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25),
                                othermonthforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 1.25), 1),
                                othermonthwebackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9),
                                othermonthweforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.9), 1),
                                weekendbackground=lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8),
                                weekendforeground=lighter_col(
                                    lighter_col(SQL.get_cus_setting_values_for("Frame")[0][3], 0.8), 1),
                                selectbackground=SQL.get_cus_setting_values_for("Now_Date")[0][3],
                                selectforeground=lighter_col(SQL.get_cus_setting_values_for("Now_Date")[0][3], 1)
                                )
        self.date_e.grid(row=4, column=2, padx=5, pady=5, sticky='w')
        ttk.Spinbox(frame, from_=0, to=23, textvariable=self.e_date_h, width=2) \
            .grid(row=4, column=3, pady=5, sticky='e')
        ttk.Label(frame, text=':', style='text.TLabel').grid(row=4, column=4)
        ttk.Spinbox(frame, from_=0, to=60, textvariable=self.e_date_m, width=2) \
            .grid(row=4, column=5, pady=5, sticky='w')

        def color_chooser():
            global menu
            orig_color = self.col
            menu.send_all_back()
            self.col = askcolor(color=orig_color, title="Choose a Color")
            menu.send_all_forward()
            self.col = str(self.col[1])
            if self.col != 'None':
                window.style.configure(f'{self.col}l.TButton', foreground=f'{lighter_col(self.col, 1)}',
                                       font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
                window.style.map(f'{self.col}l.TButton', background=[('!active', f'{self.col}'),
                                                                     ('active', lighter_col(self.col, 1.1))])
                col_button.config(text=self.col, style=f'{self.col}l.TButton')
            else:
                self.col = orig_color

        # STATE LABEL AND OptionMenu
        ttk.Label(frame, text="Color:", style='text.TLabel').grid(row=5, column=0, padx=5, pady=10)
        window.style.configure(f'{self.col}l.TButton', foreground=f'{lighter_col(self.col, 1)}',
                               font=('Helvetica', 8), anchor='nw', relief='flat', padding=0)
        window.style.map(f'{self.col}l.TButton', background=[('!active', f'{self.col}'),
                                                             ('active', lighter_col(self.col, 1.1))])
        col_button = ttk.Button(frame, text=self.col, style=f'{self.col}l.TButton',
                                command=color_chooser)
        col_button.grid(row=5, column=1, columnspan=2, sticky='w')

        # ERRORS
        self.te_label = ttk.Label(frame, text=self.t_ERROR, style='error.TLabel')
        self.te_label.grid(row=2, column=1, padx=5, pady=1, sticky='w', columnspan=5)

    def occurrence_main_menu(self):
        """Initializes Repeats Menu"""
        self.page2.rowconfigure(0, weight=1)
        self.page2.columnconfigure(0, weight=1)
        self.frame_o = ttk.LabelFrame(self.page2, text='Repeats:', style='main.TLabelframe')
        self.frame_o.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        self.frame_o.rowconfigure(0, weight=1)
        self.frame_o.rowconfigure(1, weight=3)
        self.frame_o.columnconfigure(0, weight=1)
        self.frame_o.columnconfigure(1, weight=1)

        ttk.Radiobutton(self.frame_o, text='No Repeats', variable=self.o_mode, value=1, command=self.no_occurrence) \
            .grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(self.frame_o, text='Add/Edit Repeats', variable=self.o_mode, value=2,
                        command=self.run_occurrence_menu).grid(row=0, column=1, padx=5, pady=5)
        if self.o_mode.get() == 2:
            self.occurrence_menu()
        else:
            self.occurrence_menu()
            self.no_occurrence()

    def no_occurrence(self):
        """Destroys Occurrences and Widgets"""
        try:
            self.occurrence = 'N/A'
            self.frame_oo.destroy()
            self.occurrence_ran = False
        except AttributeError:
            pass

    def run_occurrence_menu(self):
        if not self.occurrence_ran:
            self.occurrence_menu()
        self.occurrence_ran = True

    def occurrence_menu(self):
        """Initializes the Main Occurrence Menu, all different widgets if user's wants it"""
        self.occurrence = event_[self.event_id].occurrence

        self.frame_oo = ttk.LabelFrame(self.frame_o, text='Repeats Menu', style='main.TLabelframe')
        self.frame_oo.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        self.frame_oo.columnconfigure(0, weight=1)
        self.frame_oo.columnconfigure(1, weight=1)
        self.frame_oo.columnconfigure(2, weight=1)
        self.frame_oo.columnconfigure(3, weight=6)

        ttk.Label(self.frame_oo, text='Repeat Every', style='text.TLabel').grid(row=0, column=0, padx=2, pady=10)

        if self.occurrence_times.get() < 0:
            self.occurrence_times.set(1)
        ttk.Spinbox(self.frame_oo, from_=0, to=99, textvariable=self.occurrence_times, width=2) \
            .grid(row=0, column=1, pady=10, sticky='w')

        occurrence_dict = {'': 'Days', 'D': 'Days', 'W': 'Weeks', 'M': 'Months', 'Y': 'Years',
                           'Days': 'Days', 'Weeks': 'Weeks', 'Months': 'Months', 'Years': 'Years'}
        occurrence_options = ['Days', 'Weeks', 'Months', 'Years']
        self.occurrence_type.set(occurrence_dict[self.occurrence_type.get()])
        ttk.OptionMenu(self.frame_oo, self.occurrence_type, self.occurrence_type.get(), *occurrence_options,
                       command=self.update_checkboxes).grid(row=0, column=2, padx=3, pady=10, sticky='w')

        # Specify Date Checkboxes
        frame_m = ttk.Frame(self.frame_oo, style='main.TFrame')
        frame_m.grid(row=1, column=0, columnspan=4, padx=4)

        frame_m.rowconfigure(0, weight=2)
        frame_m.rowconfigure(1, weight=1)
        frame_m.rowconfigure(2, weight=1)

        ttk.Label(frame_m, text='on the following days:', style='text.TLabel') \
            .grid(row=0, column=0, columnspan=5, padx=3, pady=5, sticky='w')

        # placement dict: {Day: [row, column]}
        placement = {'M': [1, 0], 'T': [1, 1], 'W': [1, 2], 't': [1, 3], 'F': [1, 4], 'S': [2, 1], 's': [2, 3]}
        for row in self.occurrences:
            # check_variables = {Day: [Checkbutton Widget, Checkbutton Variable]}
            self.check_variables[row] = ['', tk.BooleanVar()]
            if row in self.occurrence_days:
                self.check_variables[row][1].set(True)
            self.check_variables[row][0] = \
                ttk.Checkbutton(frame_m, text=self.occurrences[row], variable=self.check_variables[row][1])
            self.check_variables[row][0].grid(
                row=placement[row][0], column=placement[row][1], padx=10, pady=5, sticky='w')

        # Update the checkboxes according to original settings
        self.update_checkboxes(self.occurrence_type.get())

    def update_checkboxes(self, choice):
        """Updates checkboxes on occurrence menu"""
        self.occurrence_days = []
        for row in self.occurrences:
            if self.check_variables[row][1].get():
                self.occurrence_days.append(row)
        if choice == 'Days':
            for row in self.occurrences:
                self.check_variables[row][0]['state'] = 'disabled'
                if self.check_variables[row][1].get():
                    self.occurrence_days.append(row)
                self.check_variables[row][1].set(False)
        else:
            for row in self.occurrences:
                self.check_variables[row][0]['state'] = 'normal'
                if row in self.occurrence_days:
                    self.check_variables[row][1].set(True)

    def description_menu(self):
        """Initializes Description Menu"""
        self.page3.rowconfigure(0, weight=1)
        self.page3.columnconfigure(0, weight=1)
        frame_m = ttk.LabelFrame(self.page3, text='Description/Notes:', padding=2, style='main.TLabelframe')
        frame_m.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='NEWS')

        x_scroll = ttk.Scrollbar(frame_m, orient='horizontal')
        y_scroll = ttk.Scrollbar(frame_m, orient='vertical')

        self.description = tk.Text(frame_m, width=55, height=12, font=('Helvetica', 12),
                                   xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set, wrap='none')
        self.description.insert(tk.END, event_[self.event_id].description)
        self.description.delete('end-1c', tk.END)

        x_scroll.config(command=self.description.xview)
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.config(command=self.description.yview)
        y_scroll.pack(side='right', fill='y')
        self.description.pack()

    def delete(self):
        """Deletes this Task"""
        global menu
        SQL.delete_event(self.event_id)
        events_initialization()
        self.destroy_window()

    def apply(self):
        """Applies all changes made"""
        global SQL
        self.name.set(check_for_shortcuts(self.name.get()))
        proceed1 = True
        # Checking Subject Entry
        if self.name.get() == '':
            self.t_ERROR = 'Enter Event Name'
            self.te_label.configure(text=self.t_ERROR)
            proceed1 = False
        try:
            if not 0 <= self.s_date_h.get() <= 23 or not 0 <= self.e_date_h.get() <= 23:
                self.t_ERROR = 'Improper Time Detected'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
            elif not 0 <= self.s_date_m.get() <= 60 or not 0 <= self.e_date_m.get() <= 60:
                self.t_ERROR = 'Improper Time Detected'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
            elif datetime.datetime.strptime(f'{self.date_s.get()} {self.s_date_h.get()}:{self.s_date_m.get()}',
                                            '%d/%m/%Y %H:%M') > \
                    datetime.datetime.strptime(f'{self.date_e.get()} {self.e_date_h.get()}:{self.e_date_m.get()}',
                                               '%d/%m/%Y %H:%M'):
                self.t_ERROR = 'End Date & Time Must Be After Start Date & Time'
                self.te_label.configure(text=self.t_ERROR)
                proceed1 = False
        except tkinter.TclError:
            self.t_ERROR = 'Improper Time Detected'
            self.te_label.configure(text=self.t_ERROR)
            proceed1 = False

        if proceed1:
            self.t_ERROR = ''
            self.te_label.configure(text=self.t_ERROR)
            self.s_date = f'{self.date_s.get()} {self.s_date_h.get()}:{self.s_date_m.get()}'
            self.e_date = f'{self.date_e.get()} {self.e_date_h.get()}:{self.e_date_m.get()}'
            self.occurrence_days = []
            for row in self.occurrences:
                if self.check_variables[row][1].get():
                    self.occurrence_days.append(row)
            occurrence_dict = {'Days': 'D', 'Weeks': 'W', 'Months': 'M', 'Years': 'Y'}
            self.occurrence_type.set(occurrence_dict[self.occurrence_type.get()])
            if self.occurrence == 'N/A':
                self.occurrence = ''
            else:
                try:
                    self.occurrence_times.get()
                except tkinter.TclError:
                    self.occurrence_times.set(1)
                self.occurrence = \
                    [str(self.occurrence_times.get()), self.occurrence_type.get(), ''.join(self.occurrence_days)]
            event = Events(self.name.get(), self.s_date, self.e_date, self.orig_id, ' '.join(self.occurrence),
                           self.description.get(1.0, tk.END), self.col, self.event_id)
            event_[self.event_id] = event
            SQL.modify_event(event_[self.event_id], self.event_id)
            menu.send_all_back()
            messagebox.showinfo("Events Manager Admin", "Event Modified!")
            menu.send_all_forward()
            events_initialization()
            window.Styles()

    def update(self):
        pass

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        if menu.tabs == 1:
            self.root.destroy()
            window.pg3.enable_buttons()
            window.pg3.update()
            window.enable_notebook()
        else:
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
            self.root.destroy()
        menu.tabs -= 1


class Tk_Sub_Notify:
    """Notification Menu Functions"""

    def __init__(self, master):
        self.root = master
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.frame = ttk.Frame(self.root, relief='raised', padding=10, style='main.TFrame')
        self.frame.pack()
        ttk.Label(self.frame, text='Notifications', style='sub_heading.TLabel').grid(row=0, column=0, sticky='ew')
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=6)
        self.frame.rowconfigure(2, weight=4)
        self.frame.rowconfigure(3, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.buttons = []
        self.e_buttons = []
        self.prev_hour = tk.IntVar(self.root)

        ttk.Button(self.frame, text='Exit', command=lambda: self.destroy_window(), style='main.TButton') \
            .grid(row=3, column=0, sticky='ew')
        self.c_frame = ttk.Labelframe(self.frame, text='Events:', style='main.TLabelframe', padding=1)

        self.tree = None

        self.event_notifications()
        self.task_view_window()
        self.root.bind('<Escape>', lambda e: self.destroy_window())
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)

    def event_notifications(self):
        """Events Notifications Menu"""
        self.c_frame.grid(row=1, column=0, sticky='news')

        # Headings
        upcoming_frame = ttk.Frame(self.c_frame, style='main.TFrame', padding=2, relief='groove', width=260, height=30)
        upcoming_frame.grid(row=0, column=0)
        upcoming_frame.pack_propagate(False)
        now_frame = ttk.Frame(self.c_frame, style='main.TFrame', padding=2, relief='groove', width=260, height=30)
        now_frame.grid(row=0, column=1)
        now_frame.pack_propagate(False)
        prev_frame = ttk.Frame(self.c_frame, style='main.TFrame', padding=2, relief='groove', width=260, height=30)
        prev_frame.grid(row=0, column=2)
        prev_frame.pack_propagate(False)

        upcoming_frame1 = ttk.Frame(upcoming_frame, style='main.TFrame', relief='flat')
        upcoming_frame1.pack(expand=1, anchor='nw')
        ttk.Label(upcoming_frame1, text='In 24 Hours:', style='text.TLabel').grid(row=0, column=0)
        # ttk.Spinbox(upcoming_frame1, textvariable=self.prev_hour, from_=1, to=99, width=2) \
        #     .grid(row=0, column=1, padx=2)
        # ttk.Label(upcoming_frame1, text='Hours:', style='text.TLabel').grid(row=0, column=2)
        ttk.Label(now_frame, text='Now:', style='text.TLabel').pack(anchor='nw')
        ttk.Label(prev_frame, text='Past:', style='text.TLabel').pack(anchor='nw')

        # Canvas
        canvas_height = 150
        canvas = tk.Canvas(self.c_frame, background=SQL.get_cus_setting_values_for('Frame')[0][3],
                           height=canvas_height, width=780, highlightthickness=0)
        y_scroll = ttk.Scrollbar(self.c_frame, orient='vertical', command=canvas.yview)
        y_scroll.grid(row=1, column=3, sticky='ns', padx=1)

        canvas.configure(yscrollcommand=y_scroll.set)
        canvas.grid(row=1, column=0, sticky='news', columnspan=3)
        c_frame = ttk.Frame(canvas, style='main.TFrame')
        canvas.create_window((0, 0), window=c_frame, anchor='nw')
        c_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Count n_of_events
        events_number_list = []
        for v in range(0, 3):
            events_number = 0
            for e in event_:
                event_[e].check_date_times()
                id_value_dict = {0: 'UpComing', 1: 'During', 2: 'Past'}
                if event_[e].notify == id_value_dict[v]:
                    events_number += 1
            events_number_list.append(events_number)
        height = (max(events_number_list) + 1) * 41  # Highest Number calculated for height of frames
        if height < canvas_height:
            height = canvas_height

        # Frame Formats
        upcoming1_frame = ttk.Frame(c_frame, style='main.TFrame', relief='groove', width=260, height=height, padding=3)
        upcoming1_frame.grid(row=0, column=0)
        upcoming1_frame.pack_propagate(False)
        upcoming1_frame1 = ttk.Frame(upcoming1_frame, style='main.TFrame', relief='flat')
        upcoming1_frame1.pack(expand=1, anchor='nw')
        now1_frame = ttk.Frame(c_frame, style='main.TFrame', relief='groove', width=260, height=height, padding=3)
        now1_frame.grid(row=0, column=1)
        now1_frame.pack_propagate(False)
        now1_frame1 = ttk.Frame(now1_frame, style='main.TFrame', relief='flat')
        now1_frame1.pack(expand=1, anchor='nw')
        prev1_frame = ttk.Frame(c_frame, style='main.TFrame', relief='groove', width=260, height=height, padding=3)
        prev1_frame.grid(row=0, column=2)
        prev1_frame.pack_propagate(False)
        prev1_frame1 = ttk.Frame(prev1_frame, style='main.TFrame', relief='flat')
        prev1_frame1.pack(expand=1, anchor='nw')

        for v, self.c_frame in enumerate((upcoming1_frame1, now1_frame1, prev1_frame1)):
            cols = 0
            for k in event_:
                event_[k].check_date_times()
                id_value_dict = {0: 'UpComing', 1: 'During', 2: 'Past'}
                if not event_[k].notify == id_value_dict[v]:
                    continue
                n_event = event_[k]
                self.e_buttons.append(
                    ttk.Button(self.c_frame, text=f'{n_event.name}\n{str(n_event.start_date.hour).zfill(2)}:'
                                                  f'{str(n_event.start_date.minute).zfill(2)}\t'
                                                  f'{str(n_event.start_date.day).zfill(2)}/'
                                                  f'{str(n_event.start_date.month).zfill(2)}/'
                                                  f'{n_event.start_date.year}        -\t'
                                                  f'{str(n_event.end_date.hour).zfill(2)}:'
                                                  f'{str(n_event.end_date.minute).zfill(2)}\t'
                                                  f'{str(n_event.end_date.day).zfill(2)}/'
                                                  f'{str(n_event.end_date.month).zfill(2)}/'
                                                  f'{n_event.end_date.year}',
                               style=f'{n_event.color}.TButton', command=lambda i=n_event.id: self.event_menu(i),
                               width=41))
                self.e_buttons[-1].grid(row=cols, column=0, padx=1, pady=2, sticky='we')
                cols += 1
            ttk.Label(self.c_frame, text='', style='text.TLabel').grid(row=cols + 1, column=0, pady=3)

    def task_view_window(self):
        """Functions for View Tasks Window"""
        frame = ttk.Labelframe(self.frame, text='Tasks Near Deadline:', style='main.TLabelframe', padding=1)
        frame.grid(row=2, column=0, sticky='news')
        tree_frame = ttk.Frame(frame, relief='flat', width=750, style='main.TFrame')
        tree_frame.grid(row=0, column=0, columnspan=2, sticky='NSEW', pady=5)
        x_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        y_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set, height=5)
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        self.tree['columns'] = ('Task', 'Due Date', 'Category', 'Reminders')

        # Format Columns
        self.tree.column('#0', width=170, minwidth=130, stretch=True)
        self.tree.column('Task', anchor='w', width=210, minwidth=100, stretch=True)
        self.tree.column('Due Date', anchor='w', width=100, minwidth=90, stretch=True)
        self.tree.column('Category', anchor='w', width=120, minwidth=100, stretch=True)
        self.tree.column('Reminders', anchor='w', width=180, minwidth=110, stretch=True)

        # Headings
        self.tree.heading('#0', text='Category/Subject', anchor='w')
        self.tree.heading('Task', text='Task Name', anchor='w')
        self.tree.heading('Due Date', text='Due Date', anchor='w')
        self.tree.heading('Category', text='Category', anchor='w')
        self.tree.heading('Reminders', text='Reminders', anchor='w')

        # Show Scrollbar
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.pack(side='right', fill='y')

        # Show Treeview
        self.tree.pack()
        self.tree.bind('<Double-Button-1>', lambda e: self.view_task_menu())
        self.tree.bind('<Control-1>', lambda e: self.mark_task_complete_or_incomplete())
        self.tasks_init()

    def tasks_init(self):
        """Initializes all tasks that goes into treeview"""
        pending_list = {}
        for task in assignment:
            if assignment[task].reminder != '':
                group = assignment[task].group.split('.')
                if group[-1] != '0' or len(group) > 2:
                    main_task = SQL.get_specific_task_data(4, '.'.join([group[0], '0']))[0]
                    pending_list[main_task[-1]] = assignment[main_task[-1]]
                else:
                    pending_list[task] = assignment[task]

        for task in pending_list:
            self.view_tasks(assignment[task], '')

    def view_tasks(self, task, parent):
        """Views tasks in treeview"""
        index = 0
        iid = task.id
        state = all_state_list[task.state]
        self.tree.insert(parent=parent, index=index, iid=str(iid), text=task.subject,
                         values=(task.name, task.date, state, task.reminder))

        parent = str(iid)
        for row in range(0, len(task.tasks)):
            iid = task.tasks[row].id
            state = all_state_list[task.tasks[row].state]
            try:
                self.tree.insert(parent=parent, index=index, iid=str(iid), text=task.tasks[row].subject,
                                 values=(task.tasks[row].name, task.tasks[row].date,
                                         state, task.tasks[row].reminder))
            except tkinter.TclError:
                order = task.tasks[row].group.split('.')
                self.tree.delete(iid)
                self.tree.insert(parent=parent, index=int(order[-1]), iid=str(iid),
                                 text=task.tasks[row].subject, values=(task.tasks[row].name,
                                                                       task.tasks[row].date, state,
                                                                       task.tasks[row].reminder))
                if index < 1:
                    main_task = self.tree.item(parent)
                    main_task = main_task['values']
                    self.tree.item(parent, values=(main_task[0], main_task[1], main_task[2], main_task[3]))
            index += 1

    def event_menu(self, event_id: int):
        """Shows the event menu whenever an event button is pressed"""
        self.disable_buttons()
        menu.event_window(event_id)

    def view_task_menu(self):
        """Shows task menu for task selected"""
        global menu
        if not menu.tabs > 1:
            try:
                task_id = int(self.tree.selection()[0])
                menu.task_window(task_id)
            except ValueError:
                pass
            except IndexError:
                pass

    def mark_task_complete_or_incomplete(self):
        """Marks selected task as complete or incomplete"""
        global menu
        if not menu.tabs > 1:
            try:
                task_id = int(self.tree.selection()[0])
                assignment[task_id].mark_complete_or_incomplete()
                SQL.modify_task(assignment[task_id], task_id)
                self.update_treeview()
            except ValueError:
                pass
            except IndexError:
                pass

    def update(self):
        """Updates Buttons"""
        self.c_frame.destroy()
        self.e_buttons = []
        self.c_frame = ttk.Labelframe(self.frame, text='Events:', style='main.TLabelframe', padding=1)
        self.event_notifications()
        self.update_treeview()

    def update_treeview(self):
        """Updates Treeview for new or modified assignments"""
        for category in self.tree.get_children():
            self.tree.delete(category)
        tasks_initialization()
        self.tasks_init()

    def disable_buttons(self):
        """Disables all buttons"""
        for button in self.buttons:
            button['state'] = 'disabled'
        for button in self.e_buttons:
            button['state'] = 'disabled'

    def enable_buttons(self):
        """Enables all buttons"""
        for button in self.buttons:
            button['state'] = 'normal'
        for button in self.e_buttons:
            button['state'] = 'normal'

    def destroy_window(self):
        """Destroys Window and enables buttons and tabs"""
        global menu, window
        if menu.tabs == 1:
            self.root.destroy()
            list_, page = window.get_disable_notebook_tabs()
            page_dict = (window.pg1, window.pg2, window.pg3, window.pg4)
            page_dict[page].enable_buttons()
            window.pg1.update_treeview()
            window.pg3.update()
            try:
                page_dict[page].update()
            except AttributeError:
                pass
            window.enable_notebook()
        else:
            menu.tab[menu.tabs - 1].enable_buttons()
            menu.tab[menu.tabs - 1].update()
            del menu.tab[menu.tabs]
            self.root.destroy()
        menu.tabs -= 1


# Objects (SETUP)
SQL = Database()
Now = Timetable()

# STATES
Important = State(1)
Quick_Task = State(2)
_Task_ = State(3)
Casual_Task = State(4)
Completed = State('c')
main_state_list = {
    1: 'Important', 'Important': 1,
    2: 'Quick Task', 'Quick Task': 2,
    3: 'Task', 'Task': 3,
    4: 'Casual Task', 'Casual Task': 4,
}
all_state_list = {
    '1': 'Important', 'Important': '1',
    '2': 'Quick Task', 'Quick Task': '2',
    '3': 'Task', 'Task': '3',
    '4': 'Casual Task', 'Casual Task': '4',
    '1c': 'Completed (I)', '2c': 'Completed (QT)', '3c': 'Completed (T)', '4c': 'Completed (CT)', 'c': 'Completed',
    'Completed (I)': '1c', 'Completed (QT)': '2c', 'Completed (T)': '3c', 'Completed (CT)': '4c',
}
menu = Tk_Sub_Pages()
assignment = {}
event_ = {}


# Appending Task Data from Database
def tasks_initialization():
    """Initializes task database and all assignments, including assignment groups"""
    global assignment
    assignment = {}
    task_list = SQL.get_task_data()
    for task_n in range(0, len(task_list)):
        n_task = Task(task_list[task_n][0], task_list[task_n][1], task_list[task_n][2], task_list[task_n][3],
                      task_list[task_n][4], task_list[task_n][5], task_list[task_n][6], task_list[task_n][-1])
        assignment[n_task.id] = n_task

    for tasks in assignment:
        _task_ = assignment[tasks]
        if _task_.group != 'N/A':
            task_grouped = _task_.group.split('.')
            if task_grouped[-1] != '0' or len(task_grouped) > 2:
                if task_grouped[-1] == '0':
                    main_group = _task_.main_group.split('.')
                    main_group.pop(-1)
                    main_group = '.'.join(main_group)
                    m_task = SQL.get_specific_task_data(4, '.'.join([main_group, '0']))
                else:
                    m_task = SQL.get_specific_task_data(4, '.'.join([_task_.main_group, '0']))
                if m_task:
                    assignment[m_task[0][-1]].tasks.append(_task_)
                    assignment[m_task[0][-1]].tasks_length += 1


def events_initialization():
    global event_
    event_ = {}
    events_list = SQL.get_all_events()
    for event in range(0, len(events_list)):
        n_event = Events(events_list[event][0], events_list[event][1], events_list[event][2], events_list[event][3],
                         events_list[event][4], events_list[event][5], events_list[event][6], events_list[event][-1])
        event_[n_event.id] = n_event


if __name__ == '__main__':
    tasks_initialization()
    events_initialization()
    root = tk.Tk()
    window = Tkinter(root)
    window.update_init()
    menu.update_disables()
    root.mainloop()
    SQL.close()
