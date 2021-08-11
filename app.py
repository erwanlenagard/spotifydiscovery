import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st



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
    if st.sidebar.button('Obtenir des recommandations'):

        scope = 'playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private streaming ugc-image-upload user-follow-modify user-follow-read user-library-read user-library-modify user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played'

        SPOTIPY_CLIENT_ID='c35363c3c06b4a459d30b2b4da74fd19'
        SPOTIPY_CLIENT_SECRET='eb7c7d1a84774f7b89cdfd901e2f33ec'
        SPOTIPY_REDIRECT_URI="{}".format('https://spotifydiscovery.herokuapp.com')

        print(scope)
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope))

        playlist=sp.user_playlist_create(username,name="test", public=False)
        st.write("playslist créée")


        results = sp.current_user_saved_tracks()
        for idx, item in enumerate(results['items']):
            track = item['track']
            st.write(idx, track['artists'][0]['name'], " – ", track['name'])
        
        
if __name__ == "__main__":
    main()