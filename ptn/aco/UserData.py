import re


class UserData:

    def __init__(self, info_dict=None):
        """
        Class represents a user data object as returned from the database.

        :param sqlite3.Row info_dict: A single row from the sqlite query.
        """

        if info_dict:
            # Convert the sqlite3.Row object to a dictionary
            info_dict = dict(info_dict)
        else:
            info_dict = dict()

        # Because we also pass a DB object, we should also covert those to the same fields. Check for form first,
        # DB second
        self.timestamp = info_dict.get('Timestamp', None) or info_dict.get('timestamp', None)

        # Users claim to have the member role, they might not actually have it. Track their response here
        self.user_claims_member = info_dict.get('Member', None) or info_dict.get('user_claims_member', None)

        self.discord_username = info_dict.get('Discord Username', None) or info_dict.get('discord_username', None)
        if self.discord_username:
            self.discord_username = self.discord_username.strip()

        self.ptn_nickname = info_dict.get('P.T.N. Discord Nickname', None) or info_dict.get('ptn_nickname', None)
        self.cmdr_name = info_dict.get('CMDR Name', None) or info_dict.get('cmdr_name', None)
        self.fleet_carrier_name = info_dict.get('Carrier Name', None) or info_dict.get('fleet_carrier_name', None)
        self.fleet_carrier_id = info_dict.get('Carrier ID', None) or info_dict.get('fleet_carrier_id', None)
        if self.fleet_carrier_id:
            # Cast the carrier ID to upper case for consistency
            self.fleet_carrier_id = self.fleet_carrier_id.upper()

            # make sure it matches the regex
            if not re.match(r"\w{3}-\w{3}", self.fleet_carrier_id):
                raise ValueError(f'Incompatible carrier ID found: {self.fleet_carrier_id} - {self.fleet_carrier_name}')

        self.ack = info_dict.get('Good Conduct', None) or info_dict.get('ack', None)

    def to_dictionary(self):
        """
        Formats the user data into a dictionary for easy access.

        :returns: A dictionary representation for the carrier data.
        :rtype: dict
        """
        response = {}
        for key, value in vars(self).items():
            if value is not None:
                response[key] = value
        return response

    def __str__(self):
        """
        Overloads str to return a readable object

        :rtype: str
        """
        return 'DiscordUser: {0.discord_username}, ({0.ptn_nickname}), ClaimedMember: {0.user_claims_member}' \
               'Cmdr Name: {0.cmdr_name}, FC: {0.fleet_carrier_name}, FCID: {0.fleet_carrier_id}.' \
               'ApplicationTime: {0.timestamp}. AcknowledgesRules: {0.ack}'.format(self)

    def __bool__(self):
        """
        Override boolean to check if any values are set, if yes then return True, else False, where false is an empty
        class.

        :rtype: bool
        """
        return any([value for key, value in vars(self).items() if value])

    def __eq__(self, other):
        """
        Override for equality check.

        :returns: The boolean state
        :rtype: bool
        """
        if isinstance(other, UserData):
            return self.__dict__ == other.__dict__
        return False
