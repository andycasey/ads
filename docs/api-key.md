# Getting an API token 

An Application Programming Interface (API) token is a secret, unique string that allows you to access the SAO/NASA ADS API. You need a token to access any of the API end points at SAO/NASA ADS.

Follow these steps to create and store your API token:

1. [Register or sign-in to ADS](https://ui.adsabs.harvard.edu/user/account/login) (opens this in a new window)

2. Navigate to the [Settings/API Token](https://ui.adsabs.harvard.edu/user/settings/token) page of ADS, and click the 'Generate a new key' button.

3. Write the API token to a file called `~/.ads/token`, or save it as an environment variable named `ADS_API_TOKEN`.

&nbsp;

:::{warning}
Your API token should **always** remain a secret. That means you should **never** store it in source code that is going to be accessible to anyone else. 
If you ever make your API token public by mistake, you should go back to the [API token](https://ui.adsabs.harvard.edu/user/settings/token) page
in ADS and generate a new token. This will invalidate the old (public) token.
:::
&nbsp;

Now that you have installed ``ads`` and you have a valid API token, you are ready to [start searching](search-syntax).
