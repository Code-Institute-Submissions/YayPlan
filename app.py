import os
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env

# creates an instance of flask and assign it to the app variable
app = Flask(__name__)

# Environment variables
app.config["MONGO_DBNAME"] = 'myPlanner'
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')

mongo = PyMongo(app)


# Homepage
@app.route('/')
@app.route('/start')
def start():
    return render_template('start.html')


# Page for registering a name and an event key
@app.route('/check_event_key')
def check_event_key():
    return render_template('check_event_key.html')


@app.route('/check_database', methods=["POST"])
def check_database():
    organizer_name = request.form["organizer_name"]
    event_key = request.form["event_key"]
    count_user = mongo.db.plans.count_documents((
        {"organizer_name": organizer_name,
         "event_key": event_key}))
    if count_user > 0:
        not_available_word = "This event key is not available with the organizer name. Please use a different event key."
        return render_template('check_event_key.html',
                               not_available_word=not_available_word,
                               organizer_name=organizer_name,
                               event_key=event_key)
    else:
        plans = mongo.db.plans
        plans.insert_one(request.form.to_dict())
        organizer_name = request.form["organizer_name"]
        plan_id = plans.find({"organizer_name": organizer_name}).sort(
            "_id", -1)[0]["_id"]
        return render_template('create_new_plan.html',
                               organizer_name=organizer_name,
                               plan_id=plan_id)


# Page for registering details of the event
@app.route('/update_details/<plan_id>', methods=["POST"])
def update_details(plan_id):
    list_avail = []
    for i in range(0, 6):
        each_availability = "availability_" + str(i)
        try:
            list_avail.append(request.form[each_availability])
        except:
            break
    plans = mongo.db.plans
    plans.update({'_id': ObjectId(plan_id)},
                 {'$set': {
                     'event_name': request.form["event_name"],
                     'event_description': request.form["event_description"],
                     'availabilities': list_avail,
                     'event_place': request.form["event_place"],
                     'participants': []
                 }})
    return render_template('after_creating_plan.html', plan_id=plan_id)


# Page for participants
@app.route('/update_plan_participants/<plan_id>')
def update_plan_participants(plan_id):
    the_plan = mongo.db.plans.find_one({"_id": ObjectId(plan_id)})
    range_availability = range(0, len(the_plan['availabilities']))
    if the_plan['participants'] == 0:
        range_participant = 0
    else:
        range_participant = range(0, len(the_plan['participants']))
    return render_template('update_plan_participants.html',
                           plan_id=plan_id, the_plan=the_plan,
                           range_participant=range_participant,
                           range_availability=range_availability)


# Connecting to the data base to register participants
@app.route('/update_plan_complete/<plan_id>', methods=["POST"])
def update_plan_complete(plan_id):
    i = 0
    while i < 50:
        i = i + 1
        each_participant = "participant_" + str(i)
        try:
            name_participant = request.form[each_participant]
            dict_avail = []
            for n in range(1, 6):
                participant_each_availability = "participant_" + \
                    str(i) + "_availability_" + str(n)
                try:
                    dict_avail.append(
                        request.form[participant_each_availability])
                except:
                    break
            the_plan = mongo.db.plans
            the_plan.update({'_id': ObjectId(plan_id)},
                            {'$push': {
                                "participants": {
                                    'name': name_participant,
                                    'availabilities': dict_avail,
                                    'participant_note':
                                        request.form["participant_note"]
                                }}
                             })
        except:
            continue

    return render_template('after_updating_plan.html', plan_id=plan_id)


# Delete a participant
@app.route('/delete_participant/<plan_id>', methods=["POST"])
def delete_participant(plan_id):
    mongo.db.plans.update({'_id': ObjectId(plan_id)},
                          {'$pull': {'participants': {
                              'name': request.form['edit_name']}}})
    return render_template('after_updating_plan.html', plan_id=plan_id)


# Render the template for restore plan page
@app.route('/restore_plan')
def restore_plan():
    return render_template('restore_plan.html')


# Check if the name and the event key match the data in the collection
@app.route('/restore_data', methods=["POST"])
def restore_data():
    organizer_name = request.form["organizer_name"]
    event_key = request.form["event_key"]
    count_user = mongo.db.plans.count_documents((
        {"organizer_name": organizer_name,
         "event_key": event_key}))
    if count_user > 0:
        the_plan = mongo.db.plans.find_one(
            {"organizer_name": request.form["organizer_name"],
             "event_key": request.form["event_key"]})
        plan_id = the_plan['_id']
        return render_template('restored_data.html',
                               plan_id=plan_id,
                               organizer_name=organizer_name,
                               event_key=event_key)
    else:
        not_found_message = "Either the name or the event key is wrong. Please try it again."
        return render_template('restore_plan.html',
                               not_found_message=not_found_message,
                               organizer_name=organizer_name,
                               event_key=event_key)


# Render the page for editing the existing plan from restore page
@app.route('/change_plan/<plan_id>')
def change_plan(plan_id):
    the_plan = mongo.db.plans.find_one({'_id': ObjectId(plan_id)})
    try:
        range_availability = range(0, len(the_plan['availabilities']))
        return render_template('change_plan.html',
                               the_plan=the_plan,
                               plan_id=the_plan['_id'],
                               range_availability=range_availability)
    except:
        return render_template('change_plan.html',
                               the_plan=the_plan,
                               plan_id=the_plan['_id'])


# Edit the existing plan from restore page
@app.route('/edit_yourplan/<plan_id>', methods=["POST"])
def edit_yourplan(plan_id):
    the_plan = mongo.db.plans.find_one({'_id': ObjectId(plan_id)})
    i = 0
    while i < len(the_plan['participants']):
        if request.form['edit_name'] == the_plan['participants'][i]['name']:
            dict_avail_edit = []
            for n in range(1, 6):
                each_availability = "availability_" + str(n)
                try:
                    dict_avail_edit.append(request.form[each_availability])
                except:
                    break
            updating_participant_DB = "participants." + str(i)

            mongo.db.plans.update(
                {'_id': ObjectId(plan_id)},
                {'$set': {
                    updating_participant_DB: {
                        'name': request.form['edit_name'],
                        'availabilities': dict_avail_edit,
                        'participant_note': request.form["participant_note"]
                    }}})
            i = i + 1
        else:
            i = i + 1
            continue
    return render_template('after_updating_plan.html', plan_id=plan_id)


# Render the page for updating participants from restore page
@app.route('/see_plan_from_restore/<plan_id>')
def see_plan_from_restore(plan_id):
    the_plan = mongo.db.plans.find_one({'_id': ObjectId(plan_id)})
    organizer_name = the_plan['organizer_name']
    event_key = the_plan['event_key']
    try:
        the_plan['availabilities']
        return redirect(url_for('update_plan_participants',
                                plan_id=plan_id))
    except:
        suggestion_word = "The plan is not set yet. Please go to 'Change Your Plan' link on the left."
        return render_template('restored_data.html',
                               plan_id=plan_id,
                               organizer_name=organizer_name,
                               event_key=event_key,
                               suggestion_word=suggestion_word)


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)
