import os
from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
# from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import spotipy
import uuid
from random import shuffle

import logging
import sys

# SET CALLBACK_URL="127.0.0.1"
# SET SPOTIPY_CLIENT_ID="c35363c3c06b4a459d30b2b4da74fd19"
# SET SPOTIPY_CLIENT_SECRET="eb7c7d1a84774f7b89cdfd901e2f33ec"
# SET SPOTIPY_REDIRECT_URI="127.0.0.1"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
# Bootstrap(app)



app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)
    
    
class NameForm(FlaskForm):
    name = StringField('Indiquez un nom d\'artiste', validators=[DataRequired()])
    submit = SubmitField('Obtenir des recommendations')    
    

def session_cache_path():
    return caches_folder + session.get('uuid')

@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private streaming ugc-image-upload user-follow-modify user-follow-read user-library-read user-library-modify user-read-private user-read-birthdate user-read-email user-top-read user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played',cache_handler=cache_handler, show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return render_template('index.html', me=spotify.me()["display_name"])
#     return f'<h2>Hi {spotify.me()["display_name"]}, ' \
#            f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
#            f'<a href="/create_playlist">create_playlist</a> | ' \
#            f'<a href="/playlists">my playlists</a> | ' \
#            f'<a href="/currently_playing">currently playing</a> | ' \
#            f'<a href="/current_user">me</a>' \


@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
#         return new_playlist(name)
        current_userid=spotify.me()["id"] 
        playlist_info=spotify.user_playlist_create(current_userid,name=str(name), public=False)
        tracks=get_recos(name)
        track_chunks=chunks(tracks,100)
        for chunk in track_chunks:
            spotify.user_playlist_add_tracks(current_userid, playlist_info['id'], chunk)
        return render_template('success.html', name=str(name), info_artiste="coucou")
        
        
    return render_template('form.html', form=form)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_recos(name):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    final_top_track=[]
    artist_ids=[]
    
    
    results_search=spotify.search(str(name), type='artist', limit=1)
    artistid=results_search['artists']['items'][0]['uri']
    # on cherche les artistes associés 
    related = spotify.artist_related_artists(artistid)
    for artistrelated in related['artists']:       
        artistrelated_id = artistrelated['id']
        artistrelated_uri=artistrelated['uri']
        artist_ids.append(artistrelated_id)
       
        #Pour chaque artiste lié on récupère un nombre de chanson recommandées (pas forcément de cet artiste)
        reco=spotify.recommendations(market='fr', seed_artists=[artistrelated_uri], limit=10)
        for trackreco in reco['tracks'] :
            artist_ids.append(trackreco['artists'][0]['id'])
#             trackreco_id=["spotify:track:" + trackreco['id']]
            trackreco_id=trackreco['id']
            print(trackreco_id)
            final_top_track.append(trackreco_id)

        #pour chaque artiste lié, on récupère ses 10 tops tracks
        result=spotify.artist_top_tracks(artistrelated_id, country='FR')
        for toptrack in result['tracks']:
            trackid=toptrack['id']
#             trackid=["spotify:track:" + toptrack['id']]
            final_top_track.append(trackid)
    print(final_top_track)
            
    l_top_track=list(set(final_top_track))
    shuffle(l_top_track)

        
        
    return final_top_track

    
    
    

def new_playlist(name):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    current_userid=spotify.me()["id"] 
    playlist_info=spotify.user_playlist_create(current_userid,name=str(name), public=False)
    
    return playlist_info


@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
#     app.run(threaded=True, port=int(os.environ.get("PORT",
#                                                    os.environ.get("SPOTIPY_REDIRECT_URI", 5000).split(":")[-1])))