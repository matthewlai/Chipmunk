# Copyright 2020 Matthew Lai
#
# This file is part of Chipmunk.
#
# Chipmunk is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chipmunk is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chipmunk.  If not, see <https://www.gnu.org/licenses/>.

import config

from email.message import EmailMessage
from email.utils import formatdate, parseaddr
from flask import abort, Flask, flash, g, redirect, render_template, request, session, \
	url_for
from markupsafe import escape
import secrets
import smtplib
import ssl
import sqlite3

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
Flask.secret_key = config.SECRET_KEY


def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(config.DB_PATH)

    # Try to create table. This will fail if the table already exists.
    column_desc = [
      'name TEXT',
      'email TEXT',
      'unit TEXT',
      'validated BOOLEAN',
      'validation_token TEXT'
    ]

    try:
      db.execute("CREATE TABLE registration ({})".format(','.join(column_desc)))
    except sqlite3.OperationalError:
      pass
  return db


@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.commit()
    db.close()


def SendEmail(email, subject, content, replyto = None):
  message = EmailMessage()
  message.set_content(content)
  message['Subject'] = subject
  message['From'] = config.SENDER_EMAIL
  message['To'] = email
  message['Date'] = formatdate()

  if replyto is not None and '@' in replyto:
    message['Reply-To'] = replyto

  context = ssl.create_default_context()
  if config.SMTP_MODE == "" or config.SMTP_MODE == "STARTTLS":
    smtp = smtplib.SMTP(host=config.SMTP_HOST, port=config.SMTP_PORT)
  elif config.SMTP_MODE == "SSL":
    smtp = smtplib.SMTP_SSL(host=config.SMTP_HOST, port=config.SMTP_PORT, context=context)
  else:
    raise ValueError("Server config error: Unknown SMTP_MODE: {}".format(config.SMTP_MODE))
  try:
    if config.SMTP_MODE == "STARTTLS":
      smtp.starttls(context=context)
    smtp.login(config.SMTP_USER, config.SMTP_PASS)
    smtp.send_message(message)
  finally:
    smtp.quit()


def SendValidationEmail(name, email, unit, validation_token):
  validation_link = \
      config.PUBLIC_ADDR + url_for('validate', token=validation_token)

  subject = '{} Email Validation'.format(config.INSTALLATION_NAME)
  content = config.VALIDATION_EMAIL_TEMPLATE.format(
      name=name, installation_name=config.INSTALLATION_NAME,
      link = validation_link, contact_email=config.CONTACT_EMAIL)
  SendEmail(email, subject, content)


def GetAllValidatedRegistrants(unit):
  result = get_db().execute('SELECT name, email FROM registration WHERE '
                            '(validated = 1 AND unit = ?)', (unit,))
  return result.fetchall()


def GetAllRegisteredUnits():
  result = get_db().execute('SELECT DISTINCT unit FROM registration WHERE validated = 1 ORDER BY unit')
  return [ row[0] for row in result.fetchall() ]


def RedactEmail(email):
  parts = email.split('@')
  if len(parts[0]) < 2:
    parts[0] = "*" * len(parts[0])
  else:
    parts[0] = parts[0][0] + "*" * (len(parts[0]) - 2) + parts[0][-1]
  return '@'.join(parts)


def SendRegistrationListEmails(unit):
  all_registrants = GetAllValidatedRegistrants(unit)
  all_reg_str = ''
  for (name, email) in all_registrants:
    all_reg_str += '{} <{}>\n'.format(name, RedactEmail(email))

  for (name, email) in all_registrants:
    subject = '{} Registration Updated'.format(config.INSTALLATION_NAME)
    content = config.REGISTRATIONS_CHANGED_EMAIL_TEMPLATE.format(
        name=name, installation_name=config.INSTALLATION_NAME,
        unit=unit, all_reg_str=all_reg_str, contact_email=config.CONTACT_EMAIL)
    SendEmail(email, subject, content)


def HandleSignup(name, email, unit):
  if not name:
    raise ValueError("Name not specified")
  if not email:
    raise ValueError("Email not specified")
  if not unit or unit == "none":
    raise ValueError("Unit not specified")

  name = name.strip()
  if name == '':
    raise ValueError("Name is empty")

  name = name[0:config.MAX_NAME_LENGTH]
  email = email[0:config.MAX_EMAIL_LENGTH]

  if not unit in config.UNITS:
    raise ValueError("{} is invalid. Unless you are trying to break the program, this "
                     "shouldn't happen. Please contact {}.".format(unit, config.CONTACT_EMAIL))

  # See if the email already exists.
  # Using parameters should automatically sanitize inputs.
  result = get_db().execute('SELECT COUNT(*) FROM registration WHERE email = ? LIMIT 1', (email,))
  count = result.fetchone()[0]

  if count > 0:
    raise ValueError("Email already registered")

  # Send the validation email.
  # Email address is validated on client side, so if we get a bad email address, it's
  # either a typo (but still valid), or something malicious. Nothing we can do for a
  # typo, and the SMTP server should check for bad addresses. We don't need to courtesy-
  # check for the user here.
  validation_token = secrets.token_urlsafe(32)
  SendValidationEmail(name, email, unit, validation_token)

  get_db().execute('INSERT INTO registration (name, email, unit, validated, validation_token) '
                   'VALUES (?, ?, ?, ?, ?)', (name, email, unit, False, validation_token))

  app.logger.info("Signing up: {} <{}>: {}".format(name, email, unit))


def HandleNotify(sender_name, sender_email, unit, note):
  if not sender_name:
    raise ValueError("Name not specified")
  if not unit:
    raise ValueError("Unit not specified")
  if not note:
    raise ValueError("Note not specified")

  if not sender_email or not '@' in sender_email:
    sender_email = ""

  sender_name = sender_name[0:config.MAX_NAME_LENGTH]
  sender_email = sender_email[0:config.MAX_EMAIL_LENGTH]
  note = note[0:config.MAX_NOTE_LENGTH]

  sender_name = sender_name.strip()
  if sender_name == '':
    raise ValueError("Sender not specified")
  if not unit in GetAllRegisteredUnits():
    raise ValueError("Unit is invalid")
  if note == "":
    raise ValueError("Note is blank")

  registrants = GetAllValidatedRegistrants(unit)
  for (name, email) in registrants:
    subject = '{} Email Notification'.format(config.INSTALLATION_NAME)
    content = config.NOTIFICATION_EMAIL_TEMPLATE.format(
        name=name, installation_name=config.INSTALLATION_NAME, unit=unit,
        sender_name=sender_name, sender_email=sender_email, content=note,
        contact_email=config.CONTACT_EMAIL)
    SendEmail(email, subject, content, replyto=sender_email)

  app.logger.info("Notify: {} <{}>: [{}] {}".format(sender_name, sender_email, unit, note[0:256]))

@app.route('/')
def index():
  return render_template('index.html',
                         title=config.INSTALLATION_NAME,
                         units=config.UNITS,
                         registered_units=GetAllRegisteredUnits(),
                         max_name_length=config.MAX_NAME_LENGTH,
                         max_email_length=config.MAX_EMAIL_LENGTH,
                         max_note_length=config.MAX_NOTE_LENGTH,
                         contact_email=config.CONTACT_EMAIL)


@app.route('/signup', methods=['POST'])
def signup():
  try:
    HandleSignup(request.form['name'], request.form['email'], request.form['unit'])
    flash("Successfully signed up for notification. "
          "You should receive an email shortly to confirm your email address. "
          "Check your spam folder if not.")
  except ValueError as e:
    flash(str(e))
  except smtplib.SMTPRecipientsRefused as e:
    flash("Failed to send validation email: {}".format(e))
  except smtplib.SMTPException as e:
    app.logger.error("Sending email failed: {}".format(e))
    flash("Failed to send validation email due to server error. Contact admin.")
  return redirect(url_for('index'))


@app.route('/notify', methods=['POST'])
def notify():
  try:
    HandleNotify(request.form['name'], request.form['email'], request.form['unit'], request.form['note'])
    flash("Note successfully sent to users registered for {}".format(request.form['unit']))
  except ValueError as e:
    flash(str(e))
  return redirect(url_for('index'))


@app.route('/validate/<token>')
def validate(token):
  try:
    result = get_db().execute('SELECT rowid, name, email, unit FROM registration '
                              'WHERE validation_token = ? LIMIT 1', (token,))
    result = result.fetchall()
    if not result:
      raise ValueError()

    rowid, name, email, unit = result[0]
    result = get_db().execute('UPDATE registration SET validated = 1 WHERE rowid = ?', (rowid,))

    SendRegistrationListEmails(unit)
    flash('Email verified! You will receive an email if someone notifies your unit. An email will be sent with '
          'a list of other users registered for the same unit (as a security precaution). An email has also been '
          'sent to all other emails (if any) currently registered for {}.'.format(unit))
  except ValueError as e:
    flash('Invalid token.')
  except Exception as e:
    app.logger.error("Failed to validate: {}".format(e))
    flash('Server error. Please contact {}'.format(config.CONTACT_EMAIL))

  return redirect(url_for('index'))