# Copyright 2011-2012 Almira Cayetano
# Copyright 2011-2012 Christian Joy Aranas
# Copyright 2011-2012 Ma. Rowena Solamo
# Copyright 2011-2012 Rommel Feria
# Copyright 2007-2008 One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# This program is a project of the University of the Philippines, College
# of Engineering, Department of Computer Science intended for
# educational purposes. If you have any suggestions and comments, you can contact us
# with the following email addresses :
#
# Almira Cayetano - accayetano@ittc.up.edu.ph
# Christian Joy Aranas - cjmaranas@gmail.com
# Ma. Rowena Solamo - rcsolamo@dcs.upd.edu.ph
# Rommel Feria - rpferia@dcs.upd.edu.ph

import pygtk
pygtk.require('2.0')
import gtk, gobject
from Models import *
from Template import Template
import datetime
import pango
from Bundler import Bundler
from pygtk_chart import multi_bar_chart

import cjson
import telepathy
from dbus.service import method, signal
from dbus.gobject_service import ExportedGObject
import logging

from sugar.activity.activity import Activity, ActivityToolbox
from sugar.activity import activity
from sugar.graphics.alert import NotifyAlert
from sugar.presence import presenceservice
from sugar.presence.tubeconn import TubeConnection

from telepathy.interfaces import (
    CHANNEL_INTERFACE, CHANNEL_INTERFACE_GROUP, CHANNEL_TYPE_TEXT,
    CONN_INTERFACE_ALIASING)
from telepathy.constants import (
    CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES,
    CHANNEL_TEXT_MESSAGE_TYPE_NORMAL)
from telepathy.client import Connection, Channel

SERVICE = "org.laptop.ScorePad"
IFACE = SERVICE
PATH = "/org/laptop/ScorePad"

BORDER_COLOR = '#FFDE00'
BACKGROUND_COLOR = '#66CC00'
BUTTON_COLOR = '#097054'
WHITE = '#FFFFFF'
BLUE = '#82CAFA'


PROJECTLIST = []
TITLELIST = []
FRIENDSTITLELIST = []
FRIENDSPROJECTLIST = []
RUBRICLIST = []
RUBRICTITLE = []
OTHER_RUBRICLIST = []
OTHER_RUBRICTITLE = []


def xpm_label_box(xpm_filename, label_text):
    box1 = gtk.HBox(False, 0)
    
    image = gtk.Image()
    image.set_from_file(xpm_filename)

    label = gtk.Label(label_text)

    box1.pack_start(image, False, False, 0)
    if label_text != "":
        box1.pack_start(label, False, False, 3)

    image.show()
    label.show()
    
    return box1

def theme_button(button):
    
    button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(BUTTON_COLOR))
    
    return button

def image_button(button, path):
    pixbufanim = gtk.gdk.PixbufAnimation(path)
    image = gtk.Image()
    image.set_from_animation(pixbufanim)
    image.show()
    button.add(image)
    return button

def theme_box(box, color):
    eb = gtk.EventBox()
    box.set_border_width(5)
    eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(color))
    eb.add(box)
    
    return eb

class ScorePadActivity(activity.Activity):
#class ScorePadActivity():
    def __init__(self, handle):
#    def __init__(self):

        logging.root.setLevel(logging.DEBUG)
        Activity.__init__(self, handle)
        self.set_title('ScorePad Activity')

        toolbox = ActivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()

        self.pservice = presenceservice.get_instance()

        owner = self.pservice.get_owner()
        self.owner = owner
        self.owner_nick = owner.props.nick
#        self.owner_nick = "cnix"
        main_canvas = self.build_root()
        self.set_canvas(main_canvas)
        main_canvas.show_all()
        #self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        #self.window.set_title("ScorePad")
        #self.window.resize(730,650)
        #self.window.add(main_canvas)
        #self.window.show_all()
        
        self.is_shared = False
        self.text_channel = None
        if self.shared_activity:
            logging.debug('Activity joined')
            self.connect('joined', self._joined_cb)
            if self.get_shared():
                self._joined_cb(self)
        else:
            logging.debug('Activity shared')
            self.connect('shared', self._shared_cb)

    def build_root(self):
        logging.debug("Function: build_root")
        
        self.scorepadDB = ScorePadDB()
        is_newlycreated = self.scorepadDB.connect_db(self.owner_nick)
        if(is_newlycreated):
            template = Template(self.owner_nick, self.scorepadDB)
            logging.debug("ScorepadDB --> template")
            template.save_template()
            logging.debug("ScorepadDB -->save_template")
        
        list = self.scorepadDB.queryall_rubric(1)
        for temp in list:
            RUBRICLIST.append(temp)
            RUBRICTITLE.append(temp.title)
            
        list = self.scorepadDB.queryall_rubric(0)
        for temp in list:
            OTHER_RUBRICLIST.append(temp)
            OTHER_RUBRICTITLE.append(temp.title)
        
        list = self.scorepadDB.queryall_project(1)
        for temp in list:
            PROJECTLIST.append(temp)
            TITLELIST.append(temp.title)

        list = self.scorepadDB.queryall_project(0)
        for temp in list:
            FRIENDSPROJECTLIST.append(temp)
            FRIENDSTITLELIST.append(temp.title)
            print "friends :" +str(temp.title)
            
        self.is_owned = True
        self.category_titles = []
        self.is_exists = False
        self.rubric_received = False
        self.is_project_owned = True
        
        self.main_table = gtk.HPaned()
        self.main_table.set_position(270)
        self.main_table.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        self.main_table.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(BACKGROUND_COLOR))
        menupanel = self.build_menupanel()
        self.main_table.add1(menupanel)

        self.build_processframe("Projects")
        self.build_projectlist()
        
        main_table_eb = theme_box(self.main_table, BACKGROUND_COLOR)
        return main_table_eb
        
    def build_menupanel(self):
        logging.debug("Function: build_menupanel")
        menupanel = gtk.VBox(False,0)
        menupanel.set_border_width(2)

        logo = gtk.Image()
        logo.set_from_file("images/scorepad.png")
        logo.show()
        
        project_button = gtk.Button()
        project_button = image_button(project_button,"images/Projects.png")
        project_button = theme_button(project_button)
        project_button.connect("clicked", self.project_cb, "Projects")
        
        create_button = gtk.Button()
        create_button = image_button(create_button,"images/AddProject.png")
        create_button = theme_button(create_button)
        create_button.connect("clicked", self.addproject_cb, "Create new project")
        
        rubrics_button = gtk.Button()
        rubrics_button = image_button(rubrics_button,"images/Rubrics.png")
        rubrics_button = theme_button(rubrics_button)
        rubrics_button.connect("clicked", self.rubrics_cb, "Rubrics")
        
        menupanel.pack_start(logo,False,False,0)
        menupanel.add(project_button)
        menupanel.add(create_button)
        menupanel.add(rubrics_button)

        return menupanel
        
    def build_processframe(self,label):
        logging.debug('Function: build_processframe')
        self.processtable = gtk.Table(12,2,True)
        self.processpanel = gtk.Frame()
        self.processpanel.add(self.processtable)
        self.processpanel.set_label(label)
        self.processpanel.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        self.main_table.add2(self.processpanel)
        self.main_table.show_all()
    
    def addproject_cb(self,widget,label):
        logging.debug('Function: addproject_cb')
        entries = self.build_projectentry(label)
        finalize_button = gtk.Button()
        finalize_button = image_button(finalize_button, "images/finalize.png")
        finalize_button = theme_button(finalize_button)
        finalize_button.connect("clicked", self.finalize_cb, entries)
        box = gtk.HBox(False,0)
        box.pack_start(finalize_button,False,False,0)
        box = theme_box(box, BORDER_COLOR)
        self.processtable.attach(box, 0,3, 11,12)
        self.main_table.show_all()
        
    def build_projectentry(self,label):
        logging.debug('Function: build_projectentry')
        self.processpanel.destroy()
        self.build_processframe(label)
        title_img = gtk.Image()
        title_img.set_from_file("images/title.png")
        author_img = gtk.Image()
        author_img.set_from_file("images/author.png")
        description_img = gtk.Image()
        description_img.set_from_file("images/description.png")
        subject_img = gtk.Image()
        subject_img.set_from_file("images/subject.png")
        date_img = gtk.Image()
        date_img.set_from_file("images/date.png")
        rubric_img = gtk.Image()
        rubric_img.set_from_file("images/rubric.png")
        
        title = gtk.Entry(50)
        title.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BACKGROUND_COLOR))
        author = gtk.Entry(50)
        author.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BACKGROUND_COLOR))
        description = gtk.TextView()
        description.set_wrap_mode(gtk.WRAP_WORD)
        description.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(BLUE))
        description.set_border_width(7)
        subject = gtk.Entry(50)
        subject.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BACKGROUND_COLOR))
        publish_date = gtk.Entry(50)
        publish_date.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BACKGROUND_COLOR))
        publish_date.set_editable(False)
        rubric_combobox = gtk.ComboBox()
        rubric_list = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        rubric_combobox.pack_start(cell)
        rubric_combobox.add_attribute(cell, 'text', 0)
        
        today = datetime.datetime.now()
        publish_date.set_text(unicode(today.replace(microsecond=0)))
        
        for i in range(len(RUBRICTITLE)):
            rubric_list.append([RUBRICTITLE[i] + " - "  + RUBRICLIST[i].author])
        
        for i in range(len(OTHER_RUBRICLIST)):
            rubric_list.append([OTHER_RUBRICTITLE[i] + " - "  + OTHER_RUBRICLIST[i].author])
        
        rubric_combobox.set_model(rubric_list)
        rubric_combobox.set_active(0)
        
        label = [title_img, author_img,description_img,subject_img,date_img,rubric_img]
        entries = [title, author, description,subject,publish_date,rubric_combobox]
        j = 0
        for i in range(6):
            if j == 2:
                self.processtable.attach(label[i],0,1,j,5)
                entry = entries[i]
                entry.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BUTTON_COLOR))
                self.processtable.attach(entries[i],1,3,j,5)
                j = 4
            else :
                if i == 5:
                    self.processtable.attach(label[i],0,1,j,j+1)
                    entry = entries[i]
                    entry.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(BORDER_COLOR))
                    self.processtable.attach(entry,1,3,j,j+1)
                else :
                    self.processtable.attach(label[i],0,1,j,j+1)
                    entry = entries[i]
                    entry.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(BORDER_COLOR))
                    self.processtable.attach(entries[i],1,3,j,j+1)
            j = j+1
        
        design = gtk.Image()
        design.set_from_file("images/design1.png")
        self.processtable.attach(design,0,3,9,11)
        return entries
            
    def finalize_cb(self,widget,entries):
        logging.debug('Function: finalize_cb')
        project = self.get_entries(entries)
        
        if self.scorepadDB.project_exists(project.title, project.author):
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "The project already exists.")
            md.run()
            md.destroy()
        else:
            self.scorepadDB.insert_project(project)
            project_id = self.scorepadDB.query_maxproject()
            project.project_id = project_id
        
            rubric_id = project.rubric_id
            rubric = self.scorepadDB.query_rubric(project.rubric_id)
            #rubric = self.search_rubric(rubric_id)
            categories = self.scorepadDB.queryall_category(rubric_id)
            self.initialize_score(project, rubric, categories)
        
            TITLELIST.append(project.title)
            PROJECTLIST.append(project)
            self.processpanel.destroy()
            self.build_processframe("Projects")
            projectlist = self.build_projectpanel()
            self.processtable.attach(projectlist,0,2,0,11)
            actionpanel = self.build_project_actionpanel()
            self.processtable.attach(actionpanel,0,2,11,12)
            self.main_table.show_all()
        
    def editproject_cb(self, widget, label):
        logging.debug('Function: editproject_cb')
        try:
            if self.is_owned:
                project = PROJECTLIST[self.selected_project]
            
                entries = self.build_projectentry(label)
                update_button = gtk.Button()
                update_button = image_button(update_button,"images/update.png")
                update_button = theme_button(update_button)
                update_button.connect("clicked", self.update_cb, entries)
                box = gtk.HBox(False,0)
                box.pack_start(update_button, False,False,0)
                box = theme_box(box,BORDER_COLOR)
                self.processtable.attach(box, 0,3, 11,12)
                self.set_entries(entries, project)
                self.main_table.show_all()
            else:
                md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                                       flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                                       type = gtk.MESSAGE_INFO,\
                                       message_format = "Sorry. You cannot edit your neighbor's project.")
                md.run()
                md.destroy()
        except:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "No project selected. Please select a project first.")
            md.run()
            md.destroy()
        
    def update_cb(self,widget,entries):
        logging.debug('Function: update_cb')
        modified_project = self.get_entries(entries)
        
        project = PROJECTLIST[self.selected_project]
        modified_project.project_id = project.project_id
        self.scorepadDB.update_project(modified_project)
        
        TITLELIST[self.selected_project] = modified_project.title
        PROJECTLIST[self.selected_project] = modified_project
        self.processpanel.destroy()
        self.build_processframe("Projects")
        projectlist = self.build_projectpanel()
        self.processtable.attach(projectlist,0,2,0,11)
        actionpanel = self.build_project_actionpanel()
        self.processtable.attach(actionpanel,0,2,11,12)
        self.main_table.show_all()
        
    def set_entries(self,entries,project):
        logging.debug('Function: set_entries')
        entries[0].set_text(project.title)
        entries[1].set_text(project.author)
        buffer = entries[2].get_buffer()
        buffer.set_text(project.description)
        entries[3].set_text(project.subject)
        rubric = self.scorepadDB.query_rubric(project.rubric_id)
        #rubric = self.search_rubric(project.rubric_id)
        
        for i in range(len(RUBRICTITLE)):
            if str(rubric.title) == str(RUBRICTITLE[i]):
                active_rubric = i

        for i in range(len(OTHER_RUBRICTITLE)):
            if str(rubric.title) == str(OTHER_RUBRICTITLE[i]):
                active_rubric = i
       
        entries[4].set_text(project.publish_date)
        entries[5].set_active(active_rubric)
        
    def get_entries(self,entries):
        logging.debug('Function: get_entries')
        title = entries[0].get_text()
        author = entries[1].get_text()
        description_buffer = entries[2].get_buffer()
        start = description_buffer.get_start_iter()
        end = description_buffer.get_end_iter()
        description = description_buffer.get_text(start,end,True)
        subject = entries[3].get_text()
        publish_date = entries[4].get_text()
        model = entries[5].get_model()
        chosen_rubric = entries[5].get_active()
        rubric = model[chosen_rubric][0]
        
        print "rubricj"+str(rubric)
        for r in RUBRICLIST:
            if str(r.title)+" - " +str(r.author) == str(rubric):
                rubric_id = r.rubric_id
    
        for r2 in OTHER_RUBRICLIST:
            if str(r2.title)+" - " +str(r2.author) == str(rubric):
                rubric_id = r2.rubric_id
        
        project = Project(None,title,author,description,subject,publish_date,1,0,rubric_id,
                          self.owner_nick,"")
        return project
    
    def viewproject_details(self,widget,row,col,tuple):
        logging.debug('Function: viewproject_details')
        buffer = tuple[0]
        projectlist = tuple[1]
        buffer.set_text("")
        r = row[0]
        self.selected_project = r
        self.is_owned = tuple[2]
        project = projectlist[r]
        rubric = self.scorepadDB.query_rubric(project.rubric_id)
        #rubric = self.search_rubric(project.rubric_id)
        details ="\nTitle :\n  -"+project.title+"\n"+\
                "Author :\n  -"+project.author+"\n"+\
                "Description :\n  -"+project.description+"\n"+\
                "Subject :\n  -"+project.subject+"\n"+\
                "Date :\n  -"+str(project.publish_date)+"\n"+\
                "Rubric :\n  -"+rubric.title+"\n"
        buffer.set_text(details)
        
    def deleteproject_cb(self,widget,data=None):
        logging.debug('Function: deleteproject')
        try:
            if self.is_owned == True:
                project_id = PROJECTLIST[self.selected_project].project_id
            else:
                project_id = FRIENDSPROJECTLIST[self.selected_project].project_id
                
            warning = gtk.MessageDialog(parent = None,buttons = gtk.BUTTONS_YES_NO, \
                                    flags =gtk.DIALOG_DESTROY_WITH_PARENT,\
                                    type = gtk.MESSAGE_WARNING,\
                                    message_format = "Are you sure you want to delete the project?")
            result = warning.run()
                
            if result == gtk.RESPONSE_YES:
                print "Yes was clicked"
                if self.is_owned == True:
                    self.scorepadDB.delete_project(project_id)
                    TITLELIST.remove(TITLELIST[self.selected_project])
                    PROJECTLIST.remove(PROJECTLIST[self.selected_project])
                else:
                    self.scorepadDB.delete_project(project_id)
                    FRIENDSTITLELIST.remove(FRIENDSTITLELIST[self.selected_project])
                    FRIENDSPROJECTLIST.remove(FRIENDSPROJECTLIST[self.selected_project])
                warning.destroy()
            elif result == gtk.RESPONSE_NO:
                print "No was clicked"
                warning.destroy()   
        
            self.processpanel.destroy()
            self.build_processframe("Projects")
            projectlist = self.build_projectpanel()
            self.processtable.attach(projectlist,0,2,0,11)
            actionpanel = self.build_project_actionpanel()
            self.processtable.attach(actionpanel,0,2,11,12)
            self.main_table.show_all()
        except:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "No project selected. Please select a project first.")
            md.run()
            md.destroy()
        
    def share_cb(self,widget,data=None):

        logging.debug('Function: share_cb')

        if self.is_shared :
            if self.is_owned:
                project = PROJECTLIST[self.selected_project]
                self.scorepadDB.update_projectshare(project.project_id, 1)
                bundler = Bundler()
                project_bundle = bundler.bundle_project(project)
                rubric_id = project.rubric_id
                logging.debug("UYRUBRIC_ID :"+str(rubric_id))
                rubric = self.scorepadDB.query_rubric(rubric_id)
                logging.debug("UYRUBRIC_SHA2 :"+str(rubric.rubric_sha))
                if not rubric.is_predefined:
                    rubric_bundle = bundler.bundle_rubric(rubric)
                    categories = self.scorepadDB.queryall_category(rubric_id)
                    category_bundle = bundler.bundle_category(categories)
                    level_bundle_list = []
                    for category in categories:
                        levels = self.scorepadDB.query_level(category.category_id)
                        level_bundle = bundler.bundle_level(levels)
                        level_bundle_list.append(level_bundle)
         
                    self.sendbundle_cb(rubric_bundle)
                    for i in range(len(category_bundle)):
                        self.sendbundle_cb(category_bundle[i])
                        level_temp = level_bundle_list[i]
                        for level in level_temp:
                            self.sendbundle_cb(level)
                    self.currently_shared = project.project_sha
                    md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "The project was successfully shared!")
                    md.run()
                    md.destroy()
                    self.is_project_owned = True
                self.sendbundle_cb(project_bundle)
            else:
                md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "You cannot share your neighbor's project.")
                md.run()
                md.destroy()
        else:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "No one is connected to you. You cannot share the project.")
            md.run()
            md.destroy()
        
    def project_cb(self,widget,label):
        logging.debug('Function: project_cb')
        self.processpanel.destroy()
        self.build_processframe(label)
        self.build_projectlist()
        
    def build_projectlist(self):
        panel = self.build_projectpanel()
        panel.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        panel.set_border_width(5)
        self.processtable.attach(panel,0,2,0,11)
        actionpanel = self.build_project_actionpanel()
        self.processtable.attach(actionpanel,0,2,11,12)
        self.main_table.show_all()
    
    def build_projectpanel(self,):
        logging.debug('Function: build_projectpanel')
        vpanel = gtk.VPaned()
        vpanel.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        vpanel.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(BACKGROUND_COLOR))
        panel = gtk.HPaned()
        
        tree_store1 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        
        for project in TITLELIST:
            tree_store1.append(None, (project,None))
        tree_view1 = gtk.TreeView(tree_store1)
        tree_view1.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(BLUE))
        tree_view1.set_rules_hint(True)
        renderer1 = gtk.CellRendererText()
        project_column1 = gtk.TreeViewColumn("Projects", renderer1, text = 0)
        
        tree_view1.append_column(project_column1)
        tree_view1_scroll = gtk.ScrolledWindow()
        tree_view1_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        tree_view1_scroll.add(tree_view1)
        vpanel.add1(tree_view1_scroll)
        
        tree_store2 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        
        for friendsproject in FRIENDSTITLELIST:
            tree_store2.append(None, (friendsproject,None))
        tree_view2 = gtk.TreeView(tree_store2)
        tree_view2.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(BLUE))
        tree_view2.set_rules_hint(True)
        renderer2 = gtk.CellRendererText()
        project_column2 = gtk.TreeViewColumn("Friends' Projects", renderer2, text = 0)
        tree_view2.append_column(project_column2)
        
        tree_view2_scroll = gtk.ScrolledWindow()
        tree_view2_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        tree_view2_scroll.add(tree_view2)
        
        vpanel.set_position(350)
        vpanel.add2(tree_view2_scroll)
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        project_view = gtk.TextView()
        project_view.modify_font(pango.FontDescription('Segoe 10'))
        project_view.set_wrap_mode(gtk.WRAP_WORD)
        project_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(BLUE))
        buffer = project_view.get_buffer()
          
        sw.add(project_view)
        sw = theme_box(sw, BUTTON_COLOR)
        
        vbox = gtk.VBox(False,0)
        pdetails_img = gtk.Image()
        pdetails_img.set_from_file("images/projectdetails.png")
        vbox.pack_start(pdetails_img,False,False,0)
        vbox.add(sw)
        
        panel.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        panel.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(BLUE))
        panel.set_position(500)
        panel.add1(vpanel)
        panel.add2(vbox)
        
        tuple1 = (buffer, PROJECTLIST,True)
        tuple2 = (buffer, FRIENDSPROJECTLIST,False)
        
        tree_view1.connect("row-activated", self.viewproject_details, tuple1)
        tree_view2.connect("row-activated", self.viewproject_details, tuple2)
        
        return panel

    def build_project_actionpanel(self):
        logging.debug('Function: build_project_actionpanel')
        actionpanel = gtk.HBox(False,5)
        
        edit_button = gtk.Button()
        edit_button = image_button(edit_button,"images/edit.png")
        edit_button = theme_button(edit_button)
        edit_button.connect("clicked", self.editproject_cb, "Edit Project")
        
        share_button = gtk.Button()
        share_button = image_button(share_button,"images/share.png")
        share_button = theme_button(share_button)
        share_button.connect("clicked", self.share_cb)
        
        evaluate_button = gtk.Button()
        evaluate_button = image_button(evaluate_button,"images/evaluate.png")
        evaluate_button = theme_button(evaluate_button)
        evaluate_button.connect("clicked", self.evaluate_cb)
        
        grades_button = gtk.Button()
        grades_button = image_button(grades_button,"images/seegrades.png")
        grades_button = theme_button(grades_button)
        grades_button.connect("clicked", self.seegrades_cb)
        
        delete_button = gtk.Button()
        delete_button = image_button(delete_button,"images/delete.png")
        delete_button = theme_button(delete_button)
        delete_button.connect("clicked", self.deleteproject_cb)
        
        actionpanel.add(edit_button)
        actionpanel.add(share_button)
        actionpanel.add(evaluate_button)
        actionpanel.add(grades_button)
        actionpanel.add(delete_button)
        actionpanel.set_border_width(5)
        actionpanel = theme_box(actionpanel, BORDER_COLOR)
        
        return actionpanel
    
    def evaluate_cb(self, widget):
        logging.debug('Function: evaluate_cb')
        try:
            if self.is_owned == True:
                project = PROJECTLIST[self.selected_project]
            else:
                project = FRIENDSPROJECTLIST[self.selected_project]
            #rubric = self.search_rubric(project.rubric_id)
            rubric = self.scorepadDB.query_rubric(project.rubric_id)
            self.processpanel.destroy()
            self.build_processframe(project.title+" by "+project.author)
        
            upperbox = self.build_upper_evalbox(project)
            upperbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
    
            self.processtable.attach(upperbox,0,2,0,2)
        
            lowerbox = gtk.VPaned()
            lowerbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
            lowerbox.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(BACKGROUND_COLOR))
            rubricsbox = self.build_lower_evalbox(rubric)
        
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
            sw.add_with_viewport(rubricsbox)
            sw = theme_box(sw, BUTTON_COLOR)
            sw.set_border_width(5)
            lowerbox.add1(sw)
            
            sw2 = gtk.ScrolledWindow()
            sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self.level_view = gtk.TextView()
            self.level_view.set_border_width(10)
            self.level_view.set_wrap_mode(gtk.WRAP_WORD)
            self.level_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(BLUE))
            buffer1 = self.level_view.get_buffer()
            buffer1.set_text("Rubric description")
            sw2.add(self.level_view)
            sw2 = theme_box(sw2, BUTTON_COLOR)
            
            lowerbox.set_position(380)
            lowerbox.add2(sw2)
        
            tuple = [rubric, project]
            box = gtk.HBox(False,0)
            submit_button = gtk.Button()
            submit_button = image_button(submit_button,"images/submit.png")
            submit_button = theme_button(submit_button)
            submit_button.connect("clicked", self.submitgrade_cb, tuple)
            box.pack_start(submit_button, False, False, 0)
            box = theme_box(box, BORDER_COLOR)
        
            self.processtable.attach(lowerbox,0,2,2,11)
            self.processtable.attach(box,0,2,11,12)
            self.main_table.show_all()
        except:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "No project selected. Please select a project first.")
            md.run()
            md.destroy()
        
    def build_upper_evalbox(self,project):
        logging.debug('Function: build_upper_evalbox')
        print "nasa build upper evalbox"
        hpaned = gtk.HPaned()
        leftbox = gtk.Table(2,1,False)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        description = gtk.TextView()
        description.set_wrap_mode(gtk.WRAP_WORD)
        description.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(BLUE))
        buffer = description.get_buffer()
        buffer.set_text(project.description)
        sw.set_border_width(3)
        sw.add(description)
        
        leftbox.attach(sw,0,1,0,2)
        
        hpaned.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        hpaned.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(BACKGROUND_COLOR))
        hpaned.set_position(450)
        leftbox = theme_box(leftbox, BORDER_COLOR)
        hpaned.add1(leftbox)
        rightbox = gtk.VBox(False,0)
        #rubric = self.search_rubric(project.rubric_id)
        rubric = self.scorepadDB.query_rubric(project.rubric_id)
        rubric_label = gtk.Label("Rubric")
        rubric_entry = gtk.Entry()
        rubric_entry.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BORDER_COLOR))
        rubric_entry.set_text(rubric.title)
        rbox = gtk.HBox()
        rbox.add(rubric_label)
        rbox.add(rubric_entry)
        rightbox.add(rbox)
        date_label = gtk.Label("Date")
        date_entry = gtk.Entry()
        date_entry.modify_bg(gtk.STATE_INSENSITIVE,gtk.gdk.color_parse(BORDER_COLOR))
        date_entry.set_text(project.publish_date)
        dbox = gtk.HBox()
        dbox.add(date_label)
        dbox.add(date_entry)
        rightbox.add(dbox)
        rightbox = theme_box(rightbox, BORDER_COLOR)
        hpaned.add2(rightbox)
        hpaned.set_border_width(5)
        print "tapos ng build upper evalbox"
        return hpaned
    
    def build_lower_evalbox(self, rubric):
        logging.debug('Function: build_lower_evalbox')
        rubric_id = rubric.rubric_id
        category = self.scorepadDB.queryall_category(rubric_id) 
        row = len(category)+1
        category_id = category[0].category_id
        column = len(self.scorepadDB.query_level(category_id))+1
        
        column_names = self.scorepadDB.query_level(category_id)
        levels = []
        for i in range(column-1):
            level = []
            for j in range(row-1):
                category_id = category[j].category_id
                level_temp = self.scorepadDB.query_level(category_id)
                level.append(level_temp[i].description)                    
            levels.append(level)
    
        view = self.build_category_column(rubric, levels, column_names, column)
        return view
        
    def build_category_column(self, rubric, levels,column_names, column_count):
        logging.debug('Function: build_category_column')
        
        self.tree_store = self.create_tree_store2(column_count)

        column = []
        for i in range(len(levels)):
            column.append(levels[i])

        rubric_id = rubric.rubric_id    
        category = self.scorepadDB.queryall_category(rubric_id)    
        
        for i in range(len(category)):
            if column_count-1 == 2:
                self.tree_store.append( None, (category[i].name,None, None))
            if column_count-1 == 3:
                self.tree_store.append( None, (category[i].name,None, None,None))
            if column_count-1 == 4:
                self.tree_store.append( None, (category[i].name,None, None,None,None))
            if column_count-1 == 5:
                self.tree_store.append( None, (category[i].name,None, None,None,None,None))
            if column_count-1 == 6:
                self.tree_store.append( None, (category[i].name,None, None,None,None,None,None))
            if column_count-1 == 7:
                self.tree_store.append( None, (category[i].name,None, None,None,None,None,None,None))
            if column_count-1 == 8:
                self.tree_store.append( None, (category[i].name,None, None,None,None,None,None,None,None))
            if column_count-1 == 9:
                self.tree_store.append( None, (category[i].name,None, None,None,None,None,None,None,None,None))
        
        view = gtk.TreeView(self.tree_store)
        view.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(BLUE))
        view.set_rules_hint(True)    
        renderer = gtk.CellRendererText()
        renderer.props.wrap_width = 250
        renderer.props.wrap_mode = pango.WRAP_WORD
        
        column0 = gtk.TreeViewColumn("Category", renderer, text=0)
        #column0.set_resizable(True)
        view.append_column(column0)
        view.connect("row-activated", self.viewlevel_details, rubric_id, category)
    
        renderlist = []
        self.number_of_level = len(levels)
        for i in range(len(levels)):
            render = gtk.CellRendererToggle()
            render.set_property('indicator-size', 40)
            render.set_property('activatable', True)
            render.connect( 'toggled', self.col1_toggled_cb, i+1 )
            renderlist.append(render)
            column = gtk.TreeViewColumn(column_names[i].name, renderlist[i])
            column.add_attribute( renderlist[i], "active", i+1)
            column.set_resizable(True)
            view.append_column(column)
        return view
        
    
    def col1_toggled_cb( self, cell, path, col ):

        for i in range(self.number_of_level+1):
            if ( (self.tree_store[path][i] == True) and (i!=col) ):
                self.tree_store[path][i] = False
        
        self.tree_store[path][col] = not self.tree_store[path][col]
        return
    
    def viewlevel_details(self, widget, row, col, rubric_id, categories):
        logging.debug('Function: viewlevel_details')
        
        selected_row = row[0]
        category_id = categories[selected_row].category_id
        category_name = categories[selected_row].name
        levels = self.scorepadDB.query_level(category_id)    
        buffer = self.level_view.get_buffer()
        buffer.set_text("")
        
        details = "===" + str(category_name)+ "===\n\n"
        for level in levels:
            details = details + level.name + "\n" + \
                    " - " + level.description + "\n\n"
        buffer.set_text(details)
            
    def rubrics_cb(self,widget,label):
        logging.debug('Function: rubrics_cb')
        self.processpanel.destroy()
        self.build_processframe(label)
        self.build_rubric_box()
        
    def build_rubric_box(self):
        logging.debug('Function: build_rubric_box')
        hpaned = gtk.HPaned()
        hpaned.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
        hpaned.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(BACKGROUND_COLOR))
        hpaned.set_border_width(5)
        rubrics = RUBRICLIST
        title = RUBRICTITLE
        box1 = self.create_rubriclist(rubrics, title, "Predefined Rubrics")
        rubrics = OTHER_RUBRICLIST
        title = OTHER_RUBRICTITLE
        box2 = self.create_rubriclist(rubrics, title, "Other Rubrics")
        
        hpaned.set_position(450)
        hpaned.add1(box1)
        hpaned.add2(box2)
        
        self.processtable.attach(hpaned,0,2,0,12)
        self.main_table.show_all()
        
    def create_rubriclist(self, rubrics, title, label):
        logging.debug('Function: create_rubriclist')
        rubricsbox = gtk.VBox(False,0)
        buttons = []
        
        separator0 = gtk.HSeparator()
        rubricsbox.pack_start(separator0, False,False,2)
        label = gtk.Label(label)
        rubricsbox.pack_start(label, False,False,0)
        separator1 = gtk.HSeparator()
        rubricsbox.pack_start(separator1, False,False,2)
        
        for i in range(len(title)):
            
            for r in rubrics:
                if str(title[i]) == str(r.title):
                    rubric = r  
            button = gtk.Button()
            box = xpm_label_box( "images/green_button2.png", title[i] + " - " + str(r.author))
            button.add(box)
            button = theme_button(button)
            button.connect("clicked", self.viewrubric_cb, rubric)
            buttons.append(button)
            rubricsbox.pack_start(button,False, False,2)
            
        rubricsbox = theme_box(rubricsbox, BACKGROUND_COLOR)
        return rubricsbox
        
    def viewrubric_cb(self, widget, rubric):    
        logging.debug('Function: viewrubric_cb')
        self.processpanel.destroy()
        self.build_processframe(rubric.title + " - " + rubric.author)
        
        box = self.build_rubriclist(rubric)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(box)
        sw.set_border_width(5)
        sw = theme_box(sw, BUTTON_COLOR)
        self.processtable.attach(sw,0,2,0,11)
        
        hbox = gtk.HBox(False,0)
        remove_button = gtk.Button()
        remove_button = image_button(remove_button,"images/delete.png")
        remove_button = theme_button(remove_button)
        remove_button.connect("clicked", self.remove_rubric_cb, rubric.rubric_id)
        hbox.pack_start(remove_button,False,False,0)
        hbox = theme_box(hbox, BORDER_COLOR)
        
        self.processtable.attach(hbox,0,2,11,12)
        self.main_table.show_all()
        
    def build_rubriclist(self, rubric):
        logging.debug('Function: build_rubriclist')
        rubric_id = rubric.rubric_id
        category = self.scorepadDB.queryall_category(rubric_id) 
        row = len(category)+1
        category_id = category[0].category_id
        column = len(self.scorepadDB.query_level(category_id))+1
        
        column_names = self.scorepadDB.query_level(category_id)
        
        levels = []
                    
        for i in range(column-1):
            level = []
            for j in range(row-1):
                category_id = category[j].category_id
                level_temp = self.scorepadDB.query_level(category_id)
                level.append(level_temp[i].description)                    
            levels.append(level)
    
        view = self.build_categorylist(rubric, levels, column_names, column)
        return view
            
    def build_categorylist(self, rubric, levels,column_names,column_count):
        logging.debug('Function: build_categorylist')
        tree_store = self.create_tree_store(column_count)
        
        column = []
        for i in range(len(levels)):
            column.append(levels[i])
        
        rubric_id = rubric.rubric_id    
        category = self.scorepadDB.queryall_category(rubric_id)    
        tuple = []
        for i in range(len(category)):
            tuple = []
            cat_str = category[i].name + "  (" + str(category[i].percentage) + ")"
            logging.debug(cat_str)
            tuple.append(cat_str)
            
            for j in range(column_count-1):
                tuple.append(column[j][i])
           
            tree_store.append(None, tuple)

        view = gtk.TreeView(tree_store)
        view.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(BLUE))
        view.set_rules_hint(True)    
        renderer = gtk.CellRendererText()
        renderer.props.wrap_width = 150
        renderer.props.wrap_mode = pango.WRAP_WORD
        column0 = gtk.TreeViewColumn("Category", renderer, text=0)
        view.append_column(column0)
        
        for i in range(len(levels)):
            render = gtk.CellRendererText()
            render.props.wrap_width = 150
            render.props.wrap_mode = pango.WRAP_WORD
            column = gtk.TreeViewColumn(column_names[i].name + "  (" +str(column_names[i].points) + ")", render, text=i+1)
            view.append_column(column)
        
        return view
    
    def create_tree_store(self, c):
        
        if c == 2:
            p = gtk.TreeStore(str,str)
        elif c == 3:
            p = gtk.TreeStore(str,str,str)
        elif c == 4:
            p = gtk.TreeStore(str,str,str,str)
        elif c == 5:
            p = gtk.TreeStore(str,str,str,str,str)
        elif c == 6:
            p = gtk.TreeStore(str,str,str,str,str,str)
        elif c == 7:
            p = gtk.TreeStore(str,str,str,str,str,str,str)
        elif c == 8:
            p = gtk.TreeStore(str,str,str,str,str,str,str,str)
        elif c == 9:
            p = gtk.TreeStore(str,str,str,str,str,str,str,str,str)
            
        return p
    
    def create_tree_store2(self, c):
        b = gobject.TYPE_BOOLEAN
        
        if c == 2:
            p = gtk.TreeStore(str,b)
        elif c == 3:
            p = gtk.TreeStore(str,b,b)
        elif c == 4:
            p = gtk.TreeStore(str,b,b,b)
        elif c == 5:
            p = gtk.TreeStore(str,b,b,b,b)
        elif c == 6:
            p = gtk.TreeStore(str,b,b,b,b,b)
        elif c == 7:
            p = gtk.TreeStore(str,b,b,b,b,b,b)
        elif c == 8:
            p = gtk.TreeStore(str,b,b,b,b,b,b,b)
        elif c == 9:
            p = gtk.TreeStore(str,b,b,b,b,b,b,b,b)
        return p
    
    def remove_rubric_cb(self, widget, rubric_id):
        
        if self.scorepadDB.check_relatedproject(rubric_id):
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                               flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                               type = gtk.MESSAGE_INFO,\
                               message_format = "You cannot delete this rubric. This rubric is still used by other projects.")
            md.run()
            md.destroy()
        else:
        
            warning = gtk.MessageDialog(parent = None,buttons = gtk.BUTTONS_YES_NO, \
                                    flags =gtk.DIALOG_DESTROY_WITH_PARENT,\
                                    type = gtk.MESSAGE_WARNING,\
                                    message_format = "Are you sure you want to delete this rubric?")
            result = warning.run()
                
            if result == gtk.RESPONSE_YES:
                self.scorepadDB.delete_rubric(rubric_id)
            
                for i in range(len(RUBRICLIST)):
                    temp = RUBRICLIST[i]
                    if temp.rubric_id == rubric_id:
                        RUBRICLIST.remove(RUBRICLIST[i])
                        RUBRICTITLE.remove(RUBRICTITLE[i])

                for i in range(len(OTHER_RUBRICLIST)):
                    temp = OTHER_RUBRICLIST[i]
                    if temp.rubric_id == rubric_id:
                        OTHER_RUBRICLIST.remove(OTHER_RUBRICLIST[i])
                        OTHER_RUBRICTITLE.remove(OTHER_RUBRICTITLE[i])
            
                self.processpanel.destroy()
                self.build_processframe("Rubric List")
                self.build_rubric_box()
                warning.destroy()
            elif result == gtk.RESPONSE_NO:
                warning.destroy()
        
    def submitgrade_cb(self, widget, tuple):
        logging.debug('Function: submitgrade_cb')
        rubric = tuple[0]
        project = tuple[1]
        
        project_id = project.project_id
        rubric_id = rubric.rubric_id
        categories = self.scorepadDB.queryall_category(rubric_id)
        category_id = categories[0].category_id
        level_list = self.scorepadDB.query_level(category_id)
        
        if self.check_columns(categories, level_list):
            self.initialize_score(project, rubric, categories)
        
            level_name = ""
            for i in range(len(categories)):
                category_id = categories[i].category_id
                for j in range(len(level_list)+1):
                    if (self.tree_store[i][j] == True):
                        level_name = level_list[j-1].name
                level_id = self.scorepadDB.querylevel_id(category_id, level_name)
                score_id = self.scorepadDB.increment_scorecount(project_id, rubric_id, category_id, level_id)
                score = self.scorepadDB.query_score2(project_id, rubric_id, category_id, level_id)
                bundler = Bundler()
                score_bundle = bundler.bundle_score(score)
                logging.debug("Function: submitgrade_cb --> scorebundle : "+score_bundle)
                logging.debug('Function: submitgrade_cb --> about to send bundle')
                is_send = False
                if self.is_shared and project.is_shared:
                    self.sendbundle_cb(score_bundle)
                    logging.debug('Function: submitgrade_cb --> bundle sent')
                    is_send = True
            if is_send:
                md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                                   flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                                   type = gtk.MESSAGE_INFO,\
                                   message_format = "You have successfully evaluated the project!")
                md.run()
                md.destroy()
    
            self.processpanel.destroy()
            self.build_processframe("Projects")
            
            panel = self.build_projectpanel()
            panel.set_border_width(5)
            self.processtable.attach(panel,0,2,0,11)
            
            actionpanel = self.build_project_actionpanel()
            self.processtable.attach(actionpanel,0,2,11,12)
            
            self.main_table.show_all()
        else:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                                   flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                                   type = gtk.MESSAGE_INFO,\
                                   message_format = "Please complete the form before proceeding.")
            md.run()
            md.destroy()
        
    def check_columns(self, categories, level_list):
        counter = 0
        for i in range(len(categories)):
            for j in range(len(level_list)+1):
                if (self.tree_store[i][j] == True):
                    counter = counter +1
        if (counter == len(categories)):
            return True
        else:
            return False
    
    def initialize_score(self, project, rubric, categories):
        logging.debug('Function: initialize_score')
        project_id = project.project_id
        rubric_id = rubric.rubric_id
        
        for category in categories:
            category_id = category.category_id
            levels = self.scorepadDB.query_level(category_id)
            for level in levels:
                level_id = level.level_id
                if self.scorepadDB.score_exists(project_id, rubric_id, category_id, level_id):
                    print 'score row exists'
                else:
                    project_sha = self.scorepadDB.query_project_sha(project_id)
                    rubric_sha = self.scorepadDB.query_rubric_sha(rubric_id)
                    category_sha = self.scorepadDB.query_category_sha(category_id)
                    level_sha = self.scorepadDB.query_level_sha(level_id)
                    score = Score(None, project_id, rubric_id, category_id, level_id,
                                  str(project_sha), str(rubric_sha),str(category_sha),str(level_sha), 0)
                    self.scorepadDB.insert_score(score)
               
    def seegrades_cb(self, widget, data =None):
        logging.debug('Function: seegrades_cb')
        
        if self.is_owned == True:
            logging.debug('Function: seegrades_cb; is_owned=True')
            try:
                project = PROJECTLIST[self.selected_project]
                logging.debug("Function: seegrades_cb; project: "+ str(self.selected_project))
                rubric = self.scorepadDB.query_rubric(project.rubric_id)
                logging.debug('Function: seegrades_cb; rubric')
                self.processpanel.destroy()
                self.build_processframe(project.title+" by "+project.author)
                logging.debug('Function: seegrades_cb; build_processframe')
                upperbox = self.build_upper_evalbox(project)
                logging.debug('Function: seegrades_cb; build_upper_evalbox')
                upperbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
                self.processtable.attach(upperbox,0,2,0,2)
                self.build_lower_gradebox(project, rubric)
                logging.debug('Function: seegrades_cb; build_lower_gradebox')
            except:
                md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                                       flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                                       type = gtk.MESSAGE_INFO,\
                                       message_format = "No project selected.")
                md.run()
                md.destroy()
        else:
            md = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, \
                                       flags = gtk.DIALOG_DESTROY_WITH_PARENT, \
                                       type = gtk.MESSAGE_INFO,\
                                       message_format = "Sorry. You cannot display your neighbor's grade.")
            md.run()
            md.destroy()
            
    def build_lower_gradebox(self, project, rubric):
        logging.debug('Function: build_lower_gradebox')
        
        project_id = project.project_id
        rubric_id = rubric.rubric_id
        
        categories = self.scorepadDB.queryall_category(rubric_id)
        category_id = categories[0].category_id
        logging.debug('Function: build_lower_gradebox --> queryall_category finished')
        
        navpanel = gtk.HBox(False)
        
        left_arrow = gtk.Button()
        left_arrow = image_button(left_arrow, "images/left.png")
        left_arrow = theme_button(left_arrow)
        right_arrow = gtk.Button()
        right_arrow = image_button(right_arrow, "images/right.png")
        right_arrow = theme_button(right_arrow)
        navpanel.add(left_arrow)
        navpanel.add(right_arrow)
        navpanel = theme_box(navpanel, BORDER_COLOR)
        self.processtable.attach(navpanel,1,2,11,12)
        
        try:
            if rubric.enable_points == 1:
                gradepanel = gtk.HBox(False)
                grade_label = gtk.Label("Final Grade")
                grade = gtk.Label(str("%0.2f%%" % ( (self.compute_score(project, rubric, categories)*100))))
                gradepanel.add(grade_label)
                gradepanel.add(grade)
                gradepanel = theme_box(gradepanel, BORDER_COLOR)
                self.processtable.attach(gradepanel,0,1,11,12)
        except:
            logging.debug("Points and Percentage not set")
        
        category_list = ""
        for category in categories:
            category_list = category_list + str(category.name.replace(' ', '~&')) + " "
        level_list = ""
        levels = self.scorepadDB.query_level(category_id)
        for level in levels:
            level_list = level_list + str(level.name.replace(' ', '~&')) + " "
        self.category_length = len(categories)
        
        self.number_of_click = 3
        if ((self.category_length == 1) or (self.category_length == 2) or (self.category_length ==3)):
            barchart = self.build_barchart(category_list, categories, level_list, project_id, rubric_id)
        else :
            partial_cat_list = ""
            partial_cat_list = str(categories[0].name) + "~& " + str(categories[1].name) + "~& " + str(categories[2].name)
            partial_cat = []
            partial_cat.append(categories[0])
            partial_cat.append(categories[1])
            partial_cat.append(categories[2])
            barchart = self.build_barchart(partial_cat_list, partial_cat, level_list, project_id, rubric_id)
            
        self.chartbox = gtk.VBox()
        self.chartbox.set_border_width(5)
        self.chartbox.add(barchart)
        self.chartbox = theme_box(self.chartbox, BUTTON_COLOR)
        self.processtable.attach(self.chartbox, 0,2,2,11)
        self.main_table.show_all()
        
        navparam = [categories, level_list, project_id, rubric_id]
        right_arrow.connect("clicked", self.navigate_cb, "0", navparam)
        left_arrow.connect("clicked", self.navigate_cb, "1", navparam)
        
    def compute_score(self, project, rubric, categories):
        project_id = project.project_id
        category_id = categories[0].category_id
        rubric_id = rubric.rubric_id
        
        list = self.scorepadDB.query_level(category_id)
        
        max = 0
        for item in list:
            if max < item.points:
                max = item.points

        raw_score = 0
        denom_score = 0
        for category in categories:
            list = self.scorepadDB.query_level(category.category_id)
            per_cat_total = 0
            per_cat_total2 = 0
            for item in list:
                count = self.scorepadDB.query_score(project_id, rubric_id, category.category_id, item.level_id)
                per_level_count = count * item.points
                per_cat_total = per_cat_total + per_level_count
                per_level_count2 = count * max
                per_cat_total2 = per_cat_total2 + per_level_count2
            temp = per_cat_total * (category.percentage * 0.01)
            temp2 = per_cat_total2 * (category.percentage * 0.01)
            raw_score = raw_score + temp
            denom_score = denom_score + temp2

        final_score = raw_score/denom_score
        return final_score
    
    def navigate_cb(self, widget,position, navparam):
        categories = navparam[0]    #b
        level_list = navparam[1]    #c
        project_id = navparam[2]    #d
        rubric_id = navparam[3]     #e
        
        self.chartbox.destroy()
        self.chartbox = gtk.VBox()
        self.chartbox.set_border_width(5)
        
        if position == "0":
            self.number_of_click = self.number_of_click + 3
        else :
            self.number_of_click = self.number_of_click -3
        
        if self.number_of_click <= self.category_length and self.number_of_click != 0:
            a = ""
            a = str(categories[self.number_of_click-3].name) + "~& " + str(categories[self.number_of_click-2].name) + "~& " \
            + str(categories[self.number_of_click-1].name)
            b = []
            b.append(categories[self.number_of_click-3])
            b.append(categories[self.number_of_click-2])
            b.append(categories[self.number_of_click-1])
            barchart = self.build_barchart(a,b,level_list,project_id,rubric_id)
            self.chartbox.add(barchart)
            self.chartbox = theme_box(self.chartbox, BUTTON_COLOR)
            self.processtable.attach(self.chartbox, 0,2,2,11)
            self.main_table.show_all()
        else:
            if ((self.number_of_click - self.category_length) == 2):
                a = ""
                a = str(categories[self.category_length-1].name)
                b = []
                b.append(categories[self.category_length-1])
                barchart = self.build_barchart(a,b,level_list,project_id,rubric_id)
                self.chartbox.add(barchart)
                self.chartbox = theme_box(self.chartbox, BUTTON_COLOR)
                self.processtable.attach(self.chartbox, 0,2,2,11)
                self.main_table.show_all()
            if ((self.number_of_click - self.category_length) == 1):
                a = ""
                a = str(categories[self.category_length-2].name) + "~& " + str(categories[self.category_length-1].name)
                b = []
                b.append(categories[self.category_length-2])
                b.append(categories[self.category_length-1])
                barchart = self.build_barchart(a,b,level_list,project_id,rubric_id)
                self.chartbox.add(barchart)
                self.chartbox = theme_box(self.chartbox, BUTTON_COLOR)
                self.processtable.attach(self.chartbox, 0,2,2,11)
                self.main_table.show_all()
            else:
                logging.debug("Out of bounds")
   
    def build_barchart(self,category_list, categories, level_list, project_id, rubric_id):
        barchart = multi_bar_chart.MultiBarChart()
        barchart.title.set_text('Grades')
        barchart.set_mode(multi_bar_chart.MODE_HORIZONTAL)
        
        i = 0
        for categoryname in category_list.split():
            categoryname_label = categoryname.replace('~&',' ').capitalize()
            multibar = multi_bar_chart.BarGroup(categoryname, categoryname_label)
            category_id = categories[i].category_id
            levels_temp = self.scorepadDB.query_level(category_id)
            j = 0
            for levelname in level_list.split():
                count = 0
                level_id = levels_temp[j].level_id
                count = self.scorepadDB.query_score(project_id, rubric_id, category_id, level_id)
                levelname_label = levelname.replace('~&',' ').capitalize()
                sub_bar = multi_bar_chart.Bar(levelname, count, levelname_label)
                multibar.add_bar(sub_bar)
                print "count : " + str(count)
                j = j+1
            barchart.add_bar(multibar)
            i = i + 1
        return barchart
    
    def search_rubric(self, rubric_id):
        for element in RUBRICLIST:
            if element.rubric_id == rubric_id:
                return element
        for element in OTHER_RUBRICLIST:
            if element.rubric_id == rubric_id:
                return element
        return None
        
#    def destroy(self, widget, data=None):
#        gtk.main_quit()
        
#    def main(self):
#        gtk.main()


#if __name__ == "__main__":
#    scorepad = ScorePadActivity()
#    scorepad.main() 

    def update_status(self, nick, text):
        text = text.split("|")
        model_name = text[0]
               
        if model_name == "Project":
            self._alert("Project was shared by", nick)
            
            self.is_project_owned = False
            
            if self.rubric_received:
                if self.is_exists:
                    rubric_id = self.rubric_exists
                    logging.debug("rubric_id if not predef, exists in the list: " +str(rubric_id))
                else:
                    rubric_id = self.scorepadDB.query_maxrubric()
                    logging.debug("rubric_id if not predef, does not exists in the list: " +str(rubric_id))
            else:
                rubric_id = text[9] #predefined kasi to kaya same ng rubric_id
                logging.debug("rubric_id if predefined : " + str(rubric_id))
                
            project = Project(None, text[2], text[3], text[4], text[5],text[6],\
                              0, 1, rubric_id, text[10], text[11], text[12])
            
            if self.scorepadDB.project_exists(project.project_sha, project.author):
                print "project exists"
            else:
                self.scorepadDB.insert_project(project)    
            
                project_id = self.scorepadDB.query_maxproject()
                project = self.scorepadDB.query_project(project_id)
            
                FRIENDSPROJECTLIST.append(project)
                FRIENDSTITLELIST.append(project.title)
                self.currently_shared = project.project_sha
            
                self.processpanel.destroy()
                self.build_processframe("Projects")
                panel = self.build_projectpanel()
                panel.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BACKGROUND_COLOR))
                panel.set_border_width(5)
                self.processtable.attach(panel,0,2,0,11)
        
                actionpanel = self.build_project_actionpanel()
                self.processtable.attach(actionpanel,0,2,11,12)
        
                self.main_table.show_all()

        if model_name == "Rubric":
            logging.debug("NASA RUBRIC KA!!")
            self.rubric_received = True
            rubric = Rubric(None, text[2], text[3], text[4], 0, text[6], text[7], text[8])
            
            self.rubric_exists = self.scorepadDB.rubric_exists(rubric.rubric_sha, rubric.description)
            logging.debug("ito ang rubric_sha : "+str(rubric.rubric_sha))
            if self.rubric_exists == None:
                self.scorepadDB.insert_rubric(rubric)
                rubric_id = self.scorepadDB.query_maxrubric()
                rubric = self.scorepadDB.query_rubric(rubric_id)
                logging.debug("ito ang sa loob ng if rubric_sha : "+str(rubric.rubric_sha))
                OTHER_RUBRICLIST.append(rubric)
                OTHER_RUBRICTITLE.append(rubric.title)
                self.is_exists = False
                logging.debug("Di nag-iexists yung rubric")
            else:
                self.is_exists = True
                logging.debug("Nag-iexists yung rubric")
        
        if model_name == "Category":
            if self.is_exists == False:
                rubric_id = self.scorepadDB.query_maxrubric()
                category = Category(None, text[2], rubric_id, text[4], text[5])
                self.scorepadDB.insert_category(category)
    
        if model_name == "Level":
            if self.is_exists == False:
                rubric_id = self.scorepadDB.query_maxrubric()
                category_id = self.scorepadDB.query_maxcategory()
                level = Level(None, text[2], text[3], category_id, rubric_id, text[6], text[7])
                self.scorepadDB.insert_level(level)

        if model_name == "Score":
            project_sha = text[6]
            rubric_sha = text[7]
            category_sha = text[8]
            level_sha = text[9]
                
            if self.scorepadDB.is_ownedproject(project_sha):
                self._alert("Score received from", nick)
                logging.debug('project_sha '+str(project_sha)+'rubric_sha '+str(rubric_sha)+'category_sha '+str(category_sha)\
                          +'level_sha '+str(level_sha))
                score_id = self.scorepadDB.query_score_id(project_sha, rubric_sha, category_sha, level_sha)
                attr = self.scorepadDB.query_score_attr(score_id)
                logging.debug("Function: update_status; query_score_attr; score_id :"+str(score_id))
                self.scorepadDB.increment_scorecount(attr[0], attr[1], attr[2], attr[3])
                logging.debug('Function: update_status; increment_scorecount')
        
    def _alert(self, title, text=None):
        alert = NotifyAlert(timeout=3)
        alert.props.title = title
        alert.props.msg = text
        self.add_alert(alert)
        alert.connect('response', self._alert_cancel_cb)
        alert.show()

    def _alert_cancel_cb(self, alert, response_id):
        self.remove_alert(alert)
        
    def _shared_cb(self, sender):
        self._setup()
        self.is_shared = True
        self._alert('Shared', 'The activity is shared')

    def _setup(self):
        self.text_channel = TextChannelWrapper(
            self.shared_activity.telepathy_text_chan,
            self.shared_activity.telepathy_conn)
        self.text_channel.set_received_callback(self._received_cb)
        self._alert("Activity Shared", "Connected")
        self.shared_activity.connect('buddy-joined', self._buddy_joined_cb)
        self.shared_activity.connect('buddy-left', self._buddy_left_cb)

    def _joined_cb(self, sender):
        if not self.shared_activity:
            return
        for buddy in self.shared_activity.get_joined_buddies():
            self._buddy_already_exists(buddy)
        self.is_shared = True
        self._setup()
        self._alert("Joined", "Joined Scorepad Activity")

    def _received_cb(self, buddy, text):
        if buddy:
            if type(buddy) is dict:
                nick = buddy['nick']
            else:
                nick = buddy.props.nick
        else:
            nick = '???'
        self.update_status(str(nick),text)

    def _buddy_joined_cb(self, sender, buddy):
        if buddy == self.owner:
            return
        self._alert(str(buddy.props.nick), "joined the activity")

    def _buddy_left_cb(self, sender, buddy):
        if buddy == self.owner:
            return
        self._alert(str(buddy.props.nick), "left")

    def _buddy_already_exists(self, buddy):
        if buddy == self.owner:
            return
        self._alert(str(buddy.props.nick), "is here")

    def sendbundle_cb(self, bundle):
        text = bundle
        if text:
            if self.text_channel:
                self.text_channel.send(text)
            else:
                print "Not connected"
        self._alert("Bundle", "sent!")

class TextChannelWrapper(object):

    def __init__(self, text_chan, conn):
        self._activity_cb = None
        self._text_chan = text_chan
        self._conn = conn
        self._signal_matches = []

    def send(self, text):
        if self._text_chan is not None:
            self._text_chan[CHANNEL_TYPE_TEXT].Send(
                CHANNEL_TEXT_MESSAGE_TYPE_NORMAL, text)

    def set_received_callback(self, callback):
        if self._text_chan is None:
            return
        self._activity_cb = callback
        m = self._text_chan[CHANNEL_TYPE_TEXT].connect_to_signal('Received',
            self._received_cb)
        self._signal_matches.append(m)

    def _received_cb(self, identity, timestamp, sender, type_, flags, text):
        if self._activity_cb:
            try:
                self._text_chan[CHANNEL_INTERFACE_GROUP]
            except Exception:
                nick = self._conn[
                    CONN_INTERFACE_ALIASING].RequestAliases([sender])[0]
                buddy = {'nick': nick, 'color': '#000000,#808080'}
            else:
                buddy = self._get_buddy(sender)
            self._activity_cb(buddy, text)
            self._text_chan[
                CHANNEL_TYPE_TEXT].AcknowledgePendingMessages([identity])
        else:
            print "Disconnected"

    def _get_buddy(self, cs_handle):
        pservice = presenceservice.get_instance()
        tp_name, tp_path = pservice.get_preferred_connection()
        conn = Connection(tp_name, tp_path)
        group = self._text_chan[CHANNEL_INTERFACE_GROUP]
        my_csh = group.GetSelfHandle()
        if my_csh == cs_handle:
            handle = conn.GetSelfHandle()
        elif group.GetGroupFlags() & \
            CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES:
            handle = group.GetHandleOwners([cs_handle])[0]
        else:
            handle = cs_handle
            assert handle != 0

        return pservice.get_buddy_by_telepathy_handle(
            tp_name, tp_path, handle)
