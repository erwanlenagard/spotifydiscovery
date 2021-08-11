import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import os

caches_folder = './'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)
    
def session_cache_path():
    return caches_folder + session.get('uuid')


def main():
    #############################
    # CONFIGURATION DE LA PAGE
    #############################
    
    st.set_page_config(
        page_title="Recommandations Spotify",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.sidebar.title('Paramètres')
    st.title('Recommandations Spotify')
    username=st.sidebar.text_input("Nom d'utilisateur", value='erwan.lenagard', max_chars=None, key=None, type='default')
    
    scope = 'playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private streaming ugc-image-upload user-follow-modify user-follow-read user-library-read user-library-modify user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played'

    SPOTIPY_CLIENT_ID='c35363c3c06b4a459d30b2b4da74fd19'
    SPOTIPY_CLIENT_SECRET='eb7c7d1a84774f7b89cdfd901e2f33ec'
    SPOTIPY_REDIRECT_URI="{}".format('https://spotifydiscovery.herokuapp.com')
    
    
    #initializing spotify oauth
    oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
        )
    auth_url = oauth.get_authorize_url()
    st.write("<a href=\""+auth_url+"\" target=\"_blank\">Se connecter</a>", unsafe_allow_html=True)   
    response = st.text_input('Click the link above, then copy the URL from the new tab, paste it here, and press enter: ')
    
    
    
    
    
    
    if st.sidebar.button('Obtenir des recommandations'):


        #connect to spotify
        code = oauth.parse_response_code(response)
        st.write(code)
        token_info = oauth.get_access_token(code)
        st.write(token_info)
        token = token_info['access_token']
        st.write(token)
        sp = spotipy.Spotify(auth=token)
        st.write("connecté")
        current_user=sp.current_user()
        st.write(current_user)

        playlist=sp.user_playlist_create(current_user['id'],name="test", public=False)
        st.write(playlist)
        st.write("playslist créée")


        results = sp.current_user_saved_tracks()
        for idx, item in enumerate(results['items']):
            track = item['track']
            st.write(idx, track['artists'][0]['name'], " – ", track['name'])
        
        
if __name__ == "__main__":
    main()