#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


from ast import keyword
from dis import disco
from email.policy import default
from gettext import find
import json
from re import S
import re
from sqlite3 import connect
from unittest import result
from urllib import response
import webbrowser
from xmlrpc.client import DateTime
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import Constraint, and_, extract, select, true, values
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

show = db.Table('show',  
    db.Column('venue_id', db.Integer, db.ForeignKey('venue.id', ondelete='cascade')),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id', ondelete='cascade')),
    db.Column('start_time', db.DateTime)
    )


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(300))
    find_talent = db.Column(db.Boolean, nullable=False, default=True)
    seek_description = db.Column(db.String(500))
    # The relationship goes here
    artist = db.relationship('Artist', secondary=show, backref=db.backref('venue', lazy=True)) 

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website_link = db.Column(db.String(300))
    find_venue = db.Column(db.Boolean, nullable=False, default=True)
    seek_description = db.Column(db.String(500))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  cities_and_states = Venue.query.distinct(Venue.city, Venue.state).group_by(Venue.id, Venue.city, Venue.state).all()
  obj_vs = None
  data = []
  
  for city_and_state in cities_and_states:
    city = city_and_state.city
    state = city_and_state.state

    venues = Venue.query.filter(Venue.city == city, Venue.state == state).all()
    # Empty the list in order to add the veneues of the subsquent city and states
    a_venue = []

    for venue in venues:
      upcoming = db.session.query(show).join(Venue).filter(show.c.start_time > datetime.now()).count()
      a_venue.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': upcoming
      })
    obj_vs = {
      'city': city_and_state.city,
      'state': city_and_state.state,
      'venues': a_venue
    }
    
    data.append(obj_vs)
  return render_template('pages/venues.html', areas=data)



@app.route('/venues/search', methods=['POST'])
def search_venues():
  keyword = request.form['search_term']


  # ILIKE (case-insensitive LIKE): query.filter(User.name.ilike('%ed%'))

  values = Venue.query.filter(Venue.name.ilike('%'+ keyword + '%')).all()
  total_num_of_records = len(values)
  data = []

  for value in values:
    datum = ''
    up_shows = db.session.query(show).filter(show.c.venue_id == value.id, show.c.start_time > datetime.now()).count()
    datum = {
      'id': value.id,
      'name': value.name,
      'num_upcoming_shows': up_shows
    }
    data.append(datum)
  response={
    "count": total_num_of_records,
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  response = ''

  venue_details = Venue.query.filter(Venue.id == venue_id).first()
  past_shows = []
  venue_past_shows = db.session.query(show, Artist).join(Artist).filter(show.c.venue_id == venue_id, show.c.start_time < datetime.now())
  for past in venue_past_shows:
    past_shows.append({
      'artist_id': past.artist_id,
      'artist_name': past.Artist.name,
      'artist_image_link': past.Artist.image_link,
      'start_time': str(past.start_time)
    })


  venue_upcoming_shows = db.session.query(show, Artist).join(Artist).filter(show.c.venue_id == venue_id, show.c.start_time > datetime.now())
  upcoming_shows = [] 
  for up_show in venue_upcoming_shows:
    upcoming_shows.append({
      'artist_id': up_show.artist_id,
      'artist_name': up_show.Artist.name,
      'artist_image_link': up_show.Artist.image_link,
      'start_time': str(up_show.start_time)
    })
  # Count all past and upcoming shows for a particular venue
  count_past_shows = db.session.query(show).filter(show.c.venue_id == venue_id, show.c.start_time < datetime.now()).count()
  count_upcoming_shows = db.session.query(show).filter(show.c.venue_id == venue_id, show.c.start_time > datetime.now()).count()
  response = {
    'id': venue_id,
    'name': venue_details.name,
    'genres': json.loads(venue_details.genres),
    'address': venue_details.address,
    'city': venue_details.city,
    'state': venue_details.state,
    'phone': venue_details.phone,
    'website': venue_details.website_link,
    'facebook_link': venue_details.facebook_link,
    'seeking_talent': venue_details.find_talent,
    'seeking_description': venue_details.seek_description,
    'image_link': venue_details.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': count_past_shows,
    'upcoming_shows_count': count_upcoming_shows
  }

  return render_template('pages/show_venue.html', venue=response)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue_name = request.form['name']
  venue_city = request.form['city']
  venue_state = request.form['state']
  venue_address = request.form['address']
  venue_phone = request.form['phone']
  selectedGenres = request.form.getlist('genres')
  venue_genres = []
  for selectedGenre in selectedGenres:
    venue_genres.append(selectedGenre)
  venue_genres = json.dumps(venue_genres)
  venue_facebook_link = request.form['facebook_link']
  venue_website_link = request.form['website_link']
  venue_image_link = request.form['image_link']
  # Checking to see whether or not a value is collected from the user and make a decision 
  try:
    venue_find_talent = request.form['seeking_talent']
    if venue_find_talent == "y":
      venue_find_talent = True
  except:
    venue_find_talent = False
  venue_seek_description = request.form['seeking_description']
  
  # //Holding the data in a variable
  new_venue = Venue(name = venue_name
                    , city = venue_city
                    , state = venue_state
                    , address = venue_address
                    , phone = venue_phone
                    , genres = venue_genres
                    , facebook_link = venue_facebook_link
                    , website_link = venue_website_link
                    , image_link = venue_image_link
                    , find_talent = venue_find_talent
                    , seek_description = venue_seek_description
  )
  generated_id = 0
  try:
    db.session.add(new_venue)
    db.session.commit()
    generated_id = new_venue.id

  except:
    generated_id = -1
  finally:
    db.session.close()
  #  //Inserting the data into the database
  if generated_id > 0:
    # on successful db insert, flash success
    flash('The venue, ' + venue_name + ', was successfully listed!')
  else:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('Oops...! The venue,' + venue_name + ', could not be listed. Kindly try again!')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)
  return render_template('pages/home.html')



@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  record = Venue.query.filter(Venue.id == venue_id)
  try:
    record.delete()
    flash('The venue was successfully deleted!')
    db.session.commit()
  except:
    flash('Oops...! Could not delete the venue!')
    return redirect(url_for('show_venue', venue_id=venue_id))
  finally:
    db.session.close()

  return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  query = Artist.query.all()
  data = []
  for row in query:
    record = {
      'id': row.id,
      'name': row.name
    }
    data.append(record)
    
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  keyword = request.form['search_term']
  values = Artist.query.filter(Artist.name.ilike('%'+ keyword + '%')).all()
  total_num_of_records = len(values)
  data = []

  for value in values:
    datum = ''
    up_shows = db.session.query(show).filter(show.c.venue_id == value.id, show.c.start_time > datetime.now()).count()
    datum = {
      'id': value.id,
      'name': value.name,
      'num_upcoming_shows': up_shows
    }
    data.append(datum)
  response={
    "count": total_num_of_records,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  response = ''

  artist_details = Artist.query.filter(Artist.id == artist_id).first()
  past_shows = []
  artist_past_shows = db.session.query(show, Artist).join(Artist).filter(show.c.artist_id == artist_id, show.c.start_time < datetime.now())
  for past in artist_past_shows:
    past_shows.append({
      'artist_id': past.artist_id,
      'artist_name': past.Artist.name,
      'artist_image_link': past.Artist.image_link,
      'start_time': str(past.start_time)
    })
  artist_upcoming_shows = db.session.query(show, Artist).join(Artist).filter(show.c.artist_id == artist_id, show.c.start_time > datetime.now())
  upcoming_shows = [] 
  for up_show in artist_upcoming_shows:
    upcoming_shows.append({
      'artist_id': past.artist_id,
      'artist_name': past.Artist.name,
      'artist_image_link': past.Artist.image_link,
      'start_time': str(past.start_time)
    })
  # Count all past and upcoming shows for a particular venue
  count_past_shows = db.session.query(show).filter(show.c.artist_id == artist_id, show.c.start_time < datetime.now()).count()
  count_upcoming_shows = db.session.query(show).filter(show.c.artist_id == artist_id, show.c.start_time > datetime.now()).count()
  response = {
    'id': artist_id,
    'name': artist_details.name,
    'genres': json.loads(artist_details.genres),
    'city': artist_details.city,
    'state': artist_details.state,
    'phone': artist_details.phone,
    'website': artist_details.website_link,
    'facebook_link': artist_details.facebook_link,
    'find_venue': artist_details.find_venue,
    'seeking_description': artist_details.seek_description,
    'image_link': artist_details.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': count_past_shows,
    'upcoming_shows_count': count_upcoming_shows
  }
  return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_data = Artist.query.filter(Artist.id == artist_id).first()
  artist={
    "id": artist_data.id,
    "name": artist_data.name,
    "genres": artist_data.genres,
    "city": artist_data.city,
    "state": artist_data.state,
    "phone": artist_data.phone,
    "website": artist_data.website_link,
    "facebook_link": artist_data.facebook_link,
    "seeking_venue": artist_data.find_venue,
    "seeking_description": artist_data.seek_description,
    "image_link": artist_data.image_link
  }
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist_data = Artist.query.filter(Artist.id == artist_id).first()

  artist_data.name = request.form['name']
  artist_data.city = request.form['city']
  artist_data.state = request.form['state']
  artist_data.phone = request.form['phone']
  selectedGenres = request.form.getlist('genres')
  artist_genres = []
  for selectedGenre in selectedGenres:
    artist_genres.append(selectedGenre)
  artist_data.genres = json.dumps(artist_genres)
  artist_data.facebook_link = request.form['facebook_link']
  artist_data.website_link = request.form['website_link']
  artist_data.image_link = request.form['image_link']
  try:
    seek_venues = request.form['seeking_venue']
    if seek_venues == "y":
      seek_venues = True
  except:
    seek_venues = False
  artist_data.find_venue = seek_venues
  artist_data.seek_description = request.form['seeking_description']
  # //Holding the data in a variable
  try:
    db.session.commit()
    flash('The artist record was successfully updated!')
  except:
    flash('Oops...! The artist record could not be updated. Kindly try again!')
    return redirect(url_for('edit_artist', artist_id=artist_id))
  finally:
    db.session.close()  
  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_data = Venue.query.filter(Venue.id == venue_id).first()
  venue={
    "id": venue_data.id,
    "name": venue_data.name,
    "genres": venue_data.genres,
    "address": venue_data.address,
    "city": venue_data.city,
    "state": venue_data.state,
    "phone": venue_data.phone,
    "website": venue_data.website_link,
    "facebook_link": venue_data.facebook_link,
    "seeking_talent": venue_data.find_talent,
    "seeking_description": venue_data.seek_description,
    "image_link": venue_data.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).first()
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  selectedGenres = request.form.getlist('genres')
  venue_genres = []
  for selectedGenre in selectedGenres:
    venue_genres.append(selectedGenre)
  venue.genres = json.dumps(venue_genres)
  venue.facebook_link = request.form['facebook_link']
  venue.website_link = request.form['website_link']
  venue.image_link = request.form['image_link']
  # Checking to see whether or not a value is collected from the user and make a decision 
  try:
    venue_find_talent = request.form['seeking_talent']
    if venue_find_talent == "y":
      venue_find_talent = True
  except:
    venue_find_talent = False
  venue.find_talent = venue_find_talent
  venue.seek_description = request.form['seeking_description']
  
  # //Holding the data in a variable
 
  try:
    db.session.commit()
    flash('The venue record was successfully updated!')
  except:
    flash('Oops...! The venue record could not be updated. Kindly try again!')
    return redirect(url_for('edit_venue', venue_id=venue_id))
  finally:
    db.session.close()  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # : insert form data as a new Venue record in the db, instead
  # : modify data to be the data object returned from db insertion
  names = request.form['name']
  citys = request.form['city']
  states = request.form['state']
  phones = request.form['phone']
  selectedGenres = request.form.getlist('genres')
  venue_genres = []
  for selectedGenre in selectedGenres:
    venue_genres.append(selectedGenre)
  venue_genres = json.dumps(venue_genres)
  facebook_links = request.form['facebook_link']
  website_links = request.form['website_link']
  image_links = request.form['image_link']
  try:
    seek_venues = request.form['seeking_venue']
    if seek_venues == "y":
      seek_venues = True
  except:
    seek_venues = False
  seek_descriptions = request.form['seeking_description']
  # //Holding the data in a variable
  new_artist = Artist(name = names
                    , city = citys
                    , state = states
                    , phone = phones
                    , genres = venue_genres
                    , facebook_link = facebook_links
                    , website_link = website_links
                    , image_link = image_links
                    , find_venue = seek_venues
                    , seek_description = seek_descriptions
  )
  generated_id = 0
  try:
    db.session.add(new_artist)
    db.session.commit()
    generated_id = new_artist.id

  except:
    generated_id = -1
  finally:
    db.session.close()
  #  //Inserting the data into the database
  if generated_id > 0:
    # on successful db insert, flash success
    flash('The artist, ' + names + ', was successfully listed!')
  else:
    # : on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Oops...! The artist,' + names + ', could not be listed. Kindly try again!')
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)
  return render_template('pages/home.html')



@app.route('/artists/<int:artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
  record = Artist.query.filter(Artist.id == artist_id)
  try:
    record.delete()
    flash('The artist was successfully deleted!')
    db.session.commit()
  except:
    flash('Oops...! Could not delete the artist!')
    return redirect(url_for('show_artist', artist_id=artist_id))
  finally:
    db.session.close()

  return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows = db.session.query(show, Artist, Venue).join(Artist, Venue).order_by(show.c.start_time.desc()).all()
  data = []

  for sh in shows:
    show_record = {
      'venue_id': sh.venue_id,
      'venue_name': sh.Venue.name,
      'artist_id': sh.artist_id,
      'artist_name': sh.Artist.name,
      'artist_image_link': sh.Artist.image_link,
      'start_time': sh.start_time
    }
    data.append(show_record)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  artist_show_id = request.form['artist_id']
  venue_show_id = request.form['venue_id']
  show_start_time = request.form['start_time']

  new_show_statement = show.insert().values(artist_id = artist_show_id, venue_id = venue_show_id, start_time = show_start_time)
  try:
    db.session.execute(new_show_statement)
    db.session.commit()
    flash('The show was successfully listed!')
    flash('Oops...! The show could not be listed. Kindly try again with valid values!')
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
