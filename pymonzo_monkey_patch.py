import uuid
import requests
import pymonzo
from pymonzo.api_objects import MonzoPot
from pymonzo.exceptions import MonzoAPIError
from six.moves.urllib.parse import urljoin
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session


def pots(self, refresh=False):
    """
    Returns a list of pots owned by the currently authorised user.

    Official docs:
        https://monzo.com/docs/#pots

    :param refresh: decides if the pots information should be refreshed.
    :type refresh: bool
    :returns: list of Monzo pots
    :rtype: list of MonzoPot
    """
    if not refresh and self._cached_pots:
        return self._cached_pots

    endpoint = '/pots'
    response = self._get_response(
        method='get', endpoint=endpoint,
    )

    pots_json = response.json()['pots']
    pots = [MonzoPot(data=pot, client=self) for pot in pots_json]
    self._cached_pots = pots

    return pots

def pot_deposit(self, account_id=None, pot_id=None, amount=0):
    """
        Deposit amount of money into a pot

    Official docs:
        https://monzo.com/docs/#deposit-into-a-pot

    :param account_id: The account id to withdraw from
    :type refresh: unicode
    :param pot_id: The target pot id
    :type pot_id: unicode
    :param amount: The amount to transfer
    :type amount: int
    :returns: updated MonzoPot
    :rtype: MonzoPot
    """

    endpoint = '/pots/{pot_id}/deposit'.format(pot_id=pot_id)
    data = {'source_account_id': account_id,
            'amount': amount,
            'dedupe_id': str(uuid.uuid4())}

    response = self._get_response(method='put', endpoint=endpoint, data=data)

    response_json = response.json()
    return MonzoPot(data=response_json, client=self)

def pot_withdraw(self, account_id=None, pot_id=None, amount=0):
    """
       Withdraw money from a pot

    Official docs:
        https://monzo.com/docs/#withdraw-from-a-pot

    :param account_id: The account id to deposit into
    :type refresh: unicode
    :param pot_id: The pot id to withdraw from
    :type pot_id: unicode
    :param amount: The amount to transfer
    :type amount: int
    :returns: updated MonzoPot
    :rtype: MonzoPot
    """

    endpoint = '/pots/{pot_id}/withdraw'.format(pot_id=pot_id)
    data = {'destination_account_id': account_id,
            'amount': amount,
            'dedupe_id': str(uuid.uuid4())}

    response = self._get_response(method='put', endpoint=endpoint, data=data)

    response_json = response.json()
    return MonzoPot(data=response_json, client=self)

def monzopot_deposit(self, account_id, amount):
    pot = self._client.pot_deposit(account_id=account_id, pot_id=self.id, amount=amount)
    self.__update(pot)

def monzopot_withdraw(self, account_id, amount):
    pot = self._client.pot_withdraw(account_id=account_id, pot_id=self.id, amount=amount)
    self.__update(pot)

def monzopot_update(self, pot):
    self.created = pot.created
    self.updated = pot.updated
    data = pot._raw_data.copy()
    data.pop('created')
    data.pop('updated')
    self.__dict__.update(**data)

def monzopot_init(self, data, client=None):
    super(MonzoPot, self).__init__(data=data)
    self._client = client

def monzoapi_get_response(self, method, endpoint, params=None, data=None):
    """
    Helper method to handle HTTP requests and catch API errors

    :param method: valid HTTP method
    :type method: str
    :param endpoint: API endpoint
    :type endpoint: str
    :param params: extra parameters passed with the request
    :type params: dict
    :returns: API response
    :rtype: Response
    """
    url = urljoin(self.api_url, endpoint)

    try:
        if method in ['post']:
            response = getattr(self._session, method)(url, params=params, data=data)
        elif method in ['put']:
            response = getattr(self._session, method)(url, data=data)
        else:
            response = getattr(self._session, method)(url, params=params)

        if response.status_code == 401:
            raise TokenExpiredError()

    except TokenExpiredError:
        # For some reason 'requests-oauthlib' automatic token refreshing
        # doesn't work so we do it here semi-manually
        self._refresh_oath_token()

        self._session = OAuth2Session(
            client_id=self._client_id,
            token=self._token,
        )

        self._get_response(method, endpoint, params, data)


    if response.status_code != requests.codes.ok:
        raise MonzoAPIError(
            "Something went wrong: {}".format(response.json())
        )

    return response


if pymonzo.__url__ != 'https://github.com/bartonp/pymonzo':
    pymonzo.MonzoAPI.pots = pots
    pymonzo.MonzoAPI.pot_deposit = pot_deposit
    pymonzo.MonzoAPI.pot_withdraw = pot_withdraw
    pymonzo.MonzoAPI._get_response = monzoapi_get_response

    MonzoPot.__init__ = monzopot_init
    MonzoPot.deposit = monzopot_deposit
    MonzoPot.withdraw = monzopot_withdraw
    MonzoPot.__update = monzopot_update
