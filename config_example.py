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

INSTALLATION_NAME="My Installation"
PUBLIC_ADDR="http://localhost:5000"

DB_PATH="userdata.db"

# Use a cryptographically-secure randomly-generated string here, AND KEEP IT SECRET!
# For example, use: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY="CHANGE_TO_YOUR_OWN_KEY!"

UNITS=[ 'Unit A', 'Unit B', 'Unit C' ]

# Contact email for help.
CONTACT_EMAIL="admin@example.com"

# For sending validation emails.
SMTP_HOST="mail.example.com"

# Use SSL connection (not STARTTLS)
SMTP_MODE="SSL"
SMTP_PORT=465

# Use STARTTLS
# SMTP_MODE="STARTTLS"
# SMTP_PORT=587

# No encryption
# SMTP_MODE=""
# SMTP_PORT=25

SMTP_USER="username"
SMTP_PASS="password"

SENDER_EMAIL="noreply@example.com"

VALIDATION_EMAIL_TEMPLATE="""Hi {name},

Someone used your email address to sign up for {installation_name}. If it was you,
click this link to validate your email: {link}

Please copy and paste to your browser if the link doesn't work.

If not, you can safely ignore this email.

Questions? Contact: {contact_email}

Thanks
{installation_name} 
"""

REGISTRATIONS_CHANGED_EMAIL_TEMPLATE="""Hi {name},

The list of emails registered for {unit} has changed. It is now as follows:

{all_reg_str}
Questions? Contact: {contact_email}

Thanks
{installation_name}
"""

NOTIFICATION_EMAIL_TEMPLATE="""Hi {name},

You are receiving this message because you registered to receive messages for {unit}, and
someone sent a message to {unit}.

Sender: {sender_name} <{sender_email}>
Note:
{content}

You may reply to this email to contact the sender, if they supplied an email address.

Questions about the system? Contact: {contact_email}

Thanks
{installation_name}
"""

MAX_NAME_LENGTH=128
MAX_EMAIL_LENGTH=128
MAX_NOTE_LENGTH=2048