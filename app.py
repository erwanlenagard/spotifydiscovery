import os
from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,SelectMultipleField,SelectField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DecimalRangeField
import spotipy
import uuid
from random import shuffle

import pandas as pd
from pandas import json_normalize

import plotly.express as px

import datetime
import logging
import sys

# SET CALLBACK_URL="127.0.0.1"
# SET SPOTIPY_CLIENT_ID=c35363c3c06b4a459d30b2b4da74fd19
# SET SPOTIPY_CLIENT_SECRET=eb7c7d1a84774f7b89cdfd901e2f33ec
# SET SPOTIPY_REDIRECT_URI=https://127.0.0.1:5000

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
Bootstrap(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')



class AnalysisForm(FlaskForm):
    name = StringField('Indiquez un nom d\'artiste', validators=[DataRequired()])
    submit = SubmitField('Analyser sa discographie')   
    
class ArtistForm(FlaskForm):
    name = StringField('Indiquez un nom d\'artiste', validators=[DataRequired()])
    danceability = DecimalRangeField('Plutôt dansant', default=50)
    energy= DecimalRangeField('Plutôt énergiques', default=50)
    valence= DecimalRangeField('Plutôt joyeux', default=50)
    tempo= DecimalRangeField('Avec un tempo rapide', default=50)
    speechiness= DecimalRangeField('Avec des paroles', default=50)
    acousticness= DecimalRangeField('Plutôt acoustique', default=50)
    instrumentalness= DecimalRangeField('Plutôt instrumental', default=50)
    liveness= DecimalRangeField('Plutôt live', default=50)
    
    submit = SubmitField('Créer la playlist')   
    
    

    
class GenreForm(FlaskForm):
    
    name = SelectMultipleField(u'Genre', choices=[("1", "rock"), ("2","afrobeat")])
#     name=SelectField('Genre',choices=[])
#     name = StringField('Indiquez un nom d\'artiste', validators=[DataRequired()])
    nb_recos = DecimalRangeField('Nombre de titres dans la playlist', default=50)
    popularity = DecimalRangeField('Popularité', default=50)
    danceability = DecimalRangeField('Plutôt dansant', default=50)
    energy= DecimalRangeField('Plutôt énergiques', default=50)
    valence= DecimalRangeField('Plutôt joyeux', default=50)
    tempo= DecimalRangeField('Avec un tempo rapide', default=50)
    speechiness= DecimalRangeField('Avec des paroles', default=50)
    acousticness= DecimalRangeField('Plutôt acoustique', default=50)
    instrumentalness= DecimalRangeField('Plutôt instrumental', default=50)
    liveness= DecimalRangeField('Plutôt live', default=50)
    
    submit = SubmitField('Créer la playlist')    
    
   
    

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
#         return f'<a href="{auth_url}">Sign in</a>'
        return render_template('login_page.html', auth_url=auth_url)

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
#     return f'<p>pas bien</p>'
    return render_template('index.html', me=spotify.me()["display_name"])



def get_user_top_artists(limit,offset,time_range):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    artists_names=[]
    str_artists_names=''
    user_top_artists=spotify.current_user_top_artists(limit=limit, offset=offset, time_range=time_range)
    for i, item in enumerate(user_top_artists['items']):
        artist=item['name']
        artists_names.append(artist)
        str_artists_names=str_artists_names+', '+artist
    return artists_names,str_artists_names[2:]+', ...'

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    artists_names,str_artists_names=get_user_top_artists(limit=10,offset=0, time_range='medium_term')
    form = ArtistForm()
    if form.validate_on_submit():
        name = form.name.data
        danceability=round(form.danceability.data /100,1)
        energy=round(form.energy.data /100,1)
        valence=round(form.valence.data /100,1)
        tempo=round(form.tempo.data /100,1)
        speechiness=round(form.speechiness.data /100,1)
        acousticness=round(form.acousticness.data /100,1)
        instrumentalness=round(form.instrumentalness.data /100,1)
        liveness=round(form.liveness.data /100,1)

        current_userid=spotify.me()["id"] 
        playlist_info=spotify.user_playlist_create(current_userid,name=str(name), public=False)
        tracks=get_recos(name,danceability,energy,valence,tempo,speechiness,acousticness,instrumentalness,liveness)
        track_chunks=chunks(tracks,100)
        for chunk in track_chunks:
            spotify.user_playlist_add_tracks(current_userid, playlist_info['id'], chunk)
        return render_template('success.html', name=str(name), playlist_id="https://open.spotify.com/embed/playlist/"+str(playlist_info['id']))     
    return render_template('form_create_playlist.html', form=form,artists_names=str_artists_names)




@app.route('/create_genre_playlist', methods=['GET', 'POST'])
def create_genre_playlist():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    available_genres=get_recommendation_genres()
    print(available_genres, file=sys.stdout)
    form = GenreForm()
    form.name.choices = available_genres
    print(form.validate_on_submit(), file=sys.stdout)
    if form.validate_on_submit():
        name = form.name.data
        nb_recos=form.nb_recos.data 
        popularity=form.popularity.data 
        danceability=round(form.danceability.data /100,1)
        energy=round(form.energy.data /100,1)
        valence=round(form.valence.data /100,1)
        tempo=round(form.tempo.data /100,1)
        speechiness=round(form.speechiness.data /100,1)
        acousticness=round(form.acousticness.data /100,1)
        instrumentalness=round(form.instrumentalness.data /100,1)
        liveness=round(form.liveness.data /100,1)

        current_userid=spotify.me()["id"] 
        playlist_info=spotify.user_playlist_create(current_userid,name=name[0], public=False)
        tracks=get_recos_genre(name,nb_recos,popularity,danceability,energy,valence,tempo,speechiness,acousticness,instrumentalness,liveness)
        track_chunks=chunks(tracks,100)
        for chunk in track_chunks:
            spotify.user_playlist_add_tracks(current_userid, playlist_info['id'], chunk)
#         return f'<p>Coucou</p>'
        return render_template('success.html', name=str(name[0]), playlist_id="https://open.spotify.com/embed/playlist/"+str(playlist_info['id']))
#         return render_template('test.html',val=name,val2=nb_recos)
    
        
    return render_template('form_create_genre_playlist.html', form=form,available_genres=available_genres)
  


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_recos(name,danceability,energy,valence,tempo,speechiness,acousticness,instrumentalness,liveness):
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
        reco=spotify.recommendations(market='fr', seed_artists=[artistrelated_uri], limit=5,
                                     target_danceability=danceability, target_energy=energy, target_valence=valence, target_tempo=tempo,
                                     target_speechiness=speechiness, target_acousticness=acousticness,
                                     target_instrumentalness=instrumentalness, target_liveness=liveness)
        
        
        for trackreco in reco['tracks'] :
            if trackreco['artists'][0]['id'] != artistid :
                artist_ids.append(trackreco['artists'][0]['id'])
    #             trackreco_id=["spotify:track:" + trackreco['id']]
                trackreco_id=trackreco['id']
                print(trackreco_id)
                final_top_track.append(trackreco_id)

        #pour chaque artiste lié, on récupère ses 10 tops tracks
        result=spotify.artist_top_tracks(artistrelated_id, country='FR')

        for toptrack in result['tracks']:
            if toptrack['artists'][0]['id'] != artistid :
                trackid=toptrack['id']
    #             trackid=["spotify:track:" + toptrack['id']]
                final_top_track.append(trackid)
            
    l_top_track=list(set(final_top_track))
    shuffle(l_top_track)
    return l_top_track

 
def get_recommendation_genres():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    l_genres=spotify.recommendation_genre_seeds()
    t_genres=[]
    for genre in l_genres['genres']:
        t_genres.append((genre,genre))
    return t_genres
    
    
def get_recos_genre(name,nb_recos,popularity,danceability,energy,valence,tempo,speechiness,acousticness,instrumentalness,liveness):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    final_top_track=[]
    artist_ids=[]
    
    
    #Pour chaque artiste lié on récupère un nombre de chanson recommandées (pas forcément de cet artiste)
    reco=spotify.recommendations(market='fr', seed_genres=name, limit=nb_recos, target_popularity=popularity,
                                 target_danceability=danceability, target_energy=energy, target_valence=valence, target_tempo=tempo,
                                 target_speechiness=speechiness, target_acousticness=acousticness,
                                 target_instrumentalness=instrumentalness, target_liveness=liveness)
    for trackreco in reco['tracks'] :
        artist_ids.append(trackreco['artists'][0]['id'])
#             trackreco_id=["spotify:track:" + trackreco['id']]
        trackreco_id=trackreco['id']
        print(trackreco_id)
        final_top_track.append(trackreco_id)
            
    l_top_track=list(set(final_top_track))
    shuffle(l_top_track)
    return l_top_track    
    

def new_playlist(name):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    current_userid=spotify.me()["id"] 
    playlist_info=spotify.user_playlist_create(current_userid,name=str(name), public=False)
    
    return playlist_info


def parsing_top_artists(top_artist):
    img_urls=[]
    artist_names=[]
    artist_popularity=[]
    artist_followers=[]
    artist_genres=[]
    artist_href=[]
    artist_ids=[]
    chunked_img_urls=[]
    chunked_artist_names=[]
    chunked_artist_popularity=[]
    chunked_artist_followers=[]
    chunked_artist_genres=[]
    chunked_artist_href=[]
    for i, item in enumerate(top_artist['items']):
        img_urls.append(item['images'][0]['url'])
        artist_ids.append(item['id'])
        artist_names.append(item['name'])
        artist_popularity.append(str(item['popularity']))
        artist_followers.append(item['followers']['total'])
        artist_genres.append(item['genres'])
        artist_href.append(item['external_urls']['spotify'])
    
    chunked_img_urls=list(chunks(img_urls, int(round(len(img_urls)/3,0))))
    chunked_artist_ids=list(chunks(artist_ids, int(round(len(artist_ids)/3,0))))
    chunked_artist_names=list(chunks(artist_names, int(round(len(artist_names)/3,0))))
    chunked_artist_popularity=list(chunks(artist_popularity,int(round(len(artist_popularity)/3,0))))
    chunked_artist_followers=list(chunks(artist_followers, int(round(len(artist_followers)/3,0))))
    chunked_artist_genres=list(chunks(artist_genres, int(round(len(artist_genres)/3,0))))
    chunked_artist_href=list(chunks(artist_href, int(round(len(artist_href)/3,0))))
    print(chunked_artist_ids)
    return chunked_img_urls, chunked_artist_ids, chunked_artist_names, chunked_artist_popularity, chunked_artist_followers, chunked_artist_genres, chunked_artist_href



@app.route('/top_artists/<term>/<limite>', methods=['GET', 'POST'])
def top_artists(term='medium-term',limite=30):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    top_artist=spotify.current_user_top_artists(limit=int(limite),offset=0, time_range=term)
    
    chunked_img_urls, chunked_artist_ids, chunked_artist_names, chunked_artist_popularity, chunked_artist_followers, chunked_artist_genres, chunked_artist_href = parsing_top_artists(top_artist)
    
    return render_template('user_top_artists.html', id_artist=chunked_artist_ids,img= chunked_img_urls, names=chunked_artist_names, popularity=chunked_artist_popularity, followers=chunked_artist_followers, genres=chunked_artist_genres, href=chunked_artist_href)



@app.route('/top_tracks/<term>/<limite>', methods=['GET', 'POST'])
def top_tracks(term='medium-term',limite=30):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    

    top_tracks=spotify.current_user_top_tracks(limit=int(limite),offset=0, time_range=term)
    
    img_urls,artist_names,track_ids,track_popularity,track_href,album_href,artist_href,album_name,track_name = parsing_top_tracks(top_tracks)
    
    return render_template('user_top_tracks.html', img_urls=img_urls, artist_names=artist_names, track_ids=track_ids, track_popularity = track_popularity, track_href=track_href, album_href=album_href, artist_href=artist_href, album_name=album_name,track_name=track_name)



def parsing_top_tracks(top_tracks):
    img_urls=[]
    artist_names=[]
    track_ids=[]
    track_popularity=[]
    track_href=[]
    album_href=[]
    artist_href=[]
    album_name=[]
    track_name=[]
    
    chunked_img_urls=[]
    chunked_artist_names=[]
    chunked_track_ids=[]
    chunked_track_popularity=[]
    chunked_track_href=[]
    chunked_album_href=[]
    chunked_artist_href=[]
    chunked_album_name=[]
    chunked_track_name=[]
    
    for i, item in enumerate(top_tracks['items']):
        img_urls.append(item['album']['images'][0]['url'])
        artist_names.append(item['artists'][0]['name'])
        track_ids.append(item['id'])
        track_popularity.append(str(item['popularity']))
        track_href.append(item['external_urls']['spotify'])
        album_href.append(item['album']['external_urls']['spotify'])
        artist_href.append(item['artists'][0]['external_urls']['spotify'])
        album_name.append(item['album']['name'])
        track_name.append(item['name'])
                          
    
    chunked_img_urls=list(chunks(img_urls, 10))
    chunked_artist_names=list(chunks(artist_names, 10))
    chunked_track_ids=list(chunks(track_ids, 10))
    chunked_track_popularity=list(chunks(track_popularity, 10))
    chunked_track_href=list(chunks(track_href, 10))
    chunked_album_href=list(chunks(album_href, 10))
    chunked_artist_href=list(chunks(artist_href, 10))
    chunked_album_name=list(chunks(album_name, 10))
    chunked_track_name=list(chunks(track_name, 10))
    return chunked_img_urls,chunked_artist_names,chunked_track_ids,chunked_track_popularity,chunked_track_href,chunked_album_href,chunked_artist_href,chunked_album_name,chunked_track_name



@app.route('/get_recos/<type_reco>/<spotify_id>')
def create_playlist_basic_recos(type_reco,spotify_id):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    current_userid=spotify.me()["id"]
    
    if type_reco=='artist':
        info=spotify.artist(spotify_id)
    elif type_reco=='track':
        info=spotify.track(spotify_id)
    
    tracks=get_basic_recos(type_reco,spotify_id)
    
    playlist_info=spotify.user_playlist_create(current_userid,name=str(info['name']), public=False)
    
    track_chunks=chunks(tracks,100)
    for chunk in track_chunks:
        spotify.user_playlist_add_tracks(current_userid, playlist_info['id'], chunk)        
    
    return render_template('success.html', name=str(info['name']), 
                           playlist_id="https://open.spotify.com/embed/playlist/"+str(playlist_info['id']))


def get_basic_recos(type_reco,spotify_id):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    final_top_track=[]
    artist_ids=[]
    if type_reco=='artist':
        # on cherche les artistes associés 
        related = spotify.artist_related_artists(spotify_id)
        for artistrelated in related['artists']:       
            artistrelated_id = artistrelated['id']
            artistrelated_uri=artistrelated['uri']
            artist_ids.append(artistrelated_id)

            #Pour chaque artiste lié on récupère un nombre de chanson recommandées (pas forcément de cet artiste)
            reco=spotify.recommendations(market='fr', seed_artists=[artistrelated_uri], limit=10)

            for trackreco in reco['tracks'] :
                if trackreco['artists'][0]['id'] != spotify_id :
                    artist_ids.append(trackreco['artists'][0]['id'])
                    trackreco_id=trackreco['id']
                    print(trackreco_id)
                    final_top_track.append(trackreco_id)

            #pour chaque artiste lié, on récupère ses 10 tops tracks
            result=spotify.artist_top_tracks(artistrelated_id, country='FR')

            for toptrack in result['tracks']:
                if toptrack['artists'][0]['id'] != spotify_id :
                    trackid=toptrack['id']
                    final_top_track.append(trackid)
            
    elif type_reco=='track':
        reco=spotify.recommendations(market='fr', seed_tracks=[spotify_id], limit=50)

        for trackreco in reco['tracks'] :
            artist_ids.append(trackreco['artists'][0]['id'])
            trackreco_id=trackreco['id']
            print(trackreco_id)
            final_top_track.append(trackreco_id)
       
            
    l_top_track=list(set(final_top_track))
    shuffle(l_top_track)
    return l_top_track




@app.route('/artist_analysis', methods=['GET', 'POST'])
def create_artist_analysis():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    form = AnalysisForm()
    if form.validate_on_submit():
        artist_name = form.name.data
        features=analyse_artist(artist_name)
        print(features.columns)
        df_radar=features[['album_id','acousticness','danceability','energy','instrumentalness',
                'liveness','speechiness','valence']].mean().reset_index()

        timestamp=datetime.datetime.fromtimestamp(features['duration_ms'].sum()/1000.0)
        timestamp_str=str(timestamp.hour)+'h '+str(timestamp.minute)+'min'
        
        df_popularity=features[['track_id','track_name','album_name','img_album_url','track_player_url','popularity']].nlargest(5, 'popularity')
        
        
        df_danceability=features[['track_id','track_name','album_name','img_album_url','track_player_url','danceability']].nlargest(10, 'danceability')
        
        df_energy=features[['track_name','energy']].nlargest(10, 'energy')
        df_danceability=features[['track_name','danceability']].nlargest(10, 'danceability')
        
        df_keys=features['key'].value_counts(normalize=True).to_frame().reset_index()
        df_keys['index'] = df_keys['index'].replace([0,1,2,3,4,5,6,7,8,9,10,11],['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'])
        
        df_mode=features['mode'].value_counts(normalize=True).to_frame().reset_index()
        df_mode['index'] = df_mode['index'].replace([0,1],['mineur','majeur'])
        
        
        per_mineur=features[features['mode']==0]['mode'].value_counts()/len(features)
        per_mineur=per_mineur[0]
        per_majeur=1-per_mineur
        
        print(features.columns)
        
        features['id']=features.index
        
        context = {
        'data': features[['id','track_id','track_name','album_name','release_date','acousticness','danceability']].to_dict(orient = 'records'),
    }

        
        return render_template('artist_analysis.html',name=artist_name, nb_albums=len(features['album_id'].unique()),
                               nb_tracks=len(features['track_id'].unique()), time=timestamp_str, 
                               label_radar=list(df_radar['index']),val_radar=list(df_radar[0]),
                               label_top_energy=list(df_energy['track_name']),val_top_energy=list(df_energy['energy']),
                               label_key=list(df_keys['index']),val_key=list(df_keys['key'].round(3)*100),
                               label_mode=list(df_mode['index']),val_mode=list(df_mode['mode'].round(3)*100),
                               df_pop=df_popularity,df_dance=df_danceability,per_mineur=round(per_mineur,1),per_majeur=round(per_majeur,1),
                               tables=features[['id','track_id','track_name','album_name',
                                                'release_date','acousticness','danceability','energy', 'instrumentalness', 
                                                'key', 'liveness', 'loudness','mode', 'speechiness', 'tempo', 'time_signature','valence',
                                                'popularity']].to_dict(orient = 'records')
                              )    
        
    return render_template('form_analyze_artist.html', form=form)


def get_all_albums(artist_id):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    res_albums=spotify.artist_albums(artist_id,album_type="album",country ='fr',limit=50)
    all_albums=res_albums['items']
    while res_albums['next'] is not None:
        res_albums=spotify.next(res_albums)
        all_albums.extend(res_albums['items'])
    return all_albums

def get_all_tracks(album_id):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
        
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    res_album_tracks=spotify.album_tracks(album_id, limit=50)
    all_tracks=res_album_tracks['items']
    while res_album_tracks['next'] is not None:
        res_album_tracks=spotify.next(res_album_tracks)
        all_tracks.extend(res_album_tracks['items'])
    return all_tracks

def radar(df_radar):
    df = pd.DataFrame(dict(
    r=list(df_radar[0]),
    theta=list(df_radar['index'])))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True)
    fig.update_traces(fill='toself')
    return fig

def parsing_track(json_track):
    all_tracks=[]
    for track in json_track['tracks']:
        track_id=track['id']
        img_album_url=track['album']['images'][0]['url']
        album_player_url=track['album']['external_urls']['spotify']
        popularity=track['popularity']
        current_track=(track_id,img_album_url,album_player_url,popularity)
        all_tracks.append(current_track)

    df_tracks=pd.DataFrame.from_records(all_tracks,columns=['track_id','img_album_url','album_player_url','popularity'])    
    return df_tracks

def analyse_artist(artist_name):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    results_search=spotify.search(str(artist_name), type='artist', limit=1)

    
    #on récupère la liste des albums
    res_albums=get_all_albums(results_search['artists']['items'][0]['uri'])
    df_albums=json_normalize(res_albums)[['id','name','release_date','total_tracks']]
    
    df_albums.drop_duplicates(subset=['name'],inplace=True)
    df_tracks=pd.DataFrame()
    #on récupère la liste des tracks de l'album
    for album_id in df_albums['id'].unique():
        res_album_tracks=get_all_tracks(album_id)
        df_tracks_tmp=json_normalize(res_album_tracks)[['id','name','track_number','external_urls.spotify','duration_ms']]
        df_tracks_tmp['album_id']=album_id
        df_tracks=pd.concat([df_tracks,df_tracks_tmp],ignore_index=True,sort=True)   


    #on crée des groupes de 50 tracks
    l_tracks_50=chunks(list(df_tracks['id']),50)
    #on récupère le detail des tracks
    df_track_details=pd.DataFrame()
    for chunk in l_tracks_50:
        res_tracks=spotify.tracks(chunk,market='fr')
        df_track_details_tmp=parsing_track(res_tracks)
        df_track_details_tmp['original_id']=chunk
        df_track_details=pd.concat([df_track_details,df_track_details_tmp],ignore_index=True,sort=True) 
        
        
    #on crée des groupes de 100 tracks
    l_tracks=chunks(list(df_tracks['id']),100)

    df_features=pd.DataFrame()
    #pour chaque groupe on récupère les features de chaque track
    for chunk in l_tracks:
        res_features=spotify.audio_features(chunk)
        df_features_tmp=json_normalize(res_features)
        df_features_tmp['original_id']=chunk
        df_features=pd.concat([df_features,df_features_tmp],ignore_index=True,sort=True)  

    #on fusionne nos dataframes
    df_tracks_features=pd.merge(df_features,df_tracks, how='left', left_on='original_id',right_on='id')
    df_tracks_features=df_tracks_features.drop(columns={'id_y','duration_ms_y'}).rename(columns={'id_x':'track_id','duration_ms_x':'duration_ms'})
    df_tracks_detailed=pd.merge(df_tracks_features,df_track_details, how='left', left_on='track_id',right_on='original_id')
    df_tracks_detailed=df_tracks_detailed.drop(columns={'track_id_x','original_id_x','track_id_y'}).rename(columns={'original_id_y':'track_id'})
    df_features_vf=pd.merge(df_tracks_detailed,df_albums, how='left', left_on='album_id',right_on='id')
    df_features_vf=df_features_vf[['acousticness', 'analysis_url', 'danceability', 'duration_ms',
           'energy', 'instrumentalness', 'key', 'liveness', 'loudness',
           'mode', 'speechiness', 'tempo', 'time_signature', 'track_href', 'type',
           'uri', 'valence', 'album_id', 'external_urls.spotify',
           'name_x', 'track_number', 'name_y', 'release_date',
           'total_tracks','track_id','img_album_url','album_player_url','popularity']].rename(columns={"name_x": "track_name",
                                            "name_y": "album_name","external_urls.spotify":"track_player_url"})
    
    df_features_vf=df_features_vf.drop_duplicates()
    
    return df_features_vf

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



    
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
#     app.run(threaded=True, port=int(os.environ.get("PORT",
#                                                    os.environ.get("SPOTIPY_REDIRECT_URI", 5000).split(":")[-1])))