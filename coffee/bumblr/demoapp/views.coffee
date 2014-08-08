define (require, exports, module) ->
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  Marionette = require 'marionette'

  FormViews = require 'views/formviews'
  Templates = require 'demoapp/templates'
  Models = require 'demoapp/models'
  BaseModels = require 'models'
    
  require 'jquery-ui'
  
  class SideBarView extends Backbone.Marionette.ItemView
    template: Templates.sidebar
    events:
      'click .mainview-button': 'mainview_pressed'
      'click .dashboard-view-button': 'dashboard_view_pressed'
      'click .list-blogs-button': 'list_blogs_pressed'
      
    _navigate: (url) ->
      r = new Backbone.Router
      r.navigate url, trigger:true

    mainview_pressed: () ->
      console.log 'mainview_pressed called'
      @_navigate '#demo'
      
    dashboard_view_pressed: () ->
      console.log 'dashboard_view_pressed called'
      @_navigate '#demo/dashboard'

    list_blogs_pressed: () ->
      console.log 'list_blogs_pressed called'
      @_navigate '#demo/listblogs'
      
      
  render_calendar_event = (calEvent, element) ->
    calEvent.url = '#bumblr/viewmeeting/' + calEvent.id
    element.css
      'font-size' : '0.9em'

  calendar_view_render = (view, element) ->
    MSGBUS.commands.execute 'bumblr:maincalendar:set_date'

  loading_calendar_events = (bool) ->
    loading = $ '#loading'
    header = $ '.fc-header'
    if bool
      loading.show()
      header.hide()
    else
      loading.hide()
      header.show()
      

  class SimpleBlogInfoView extends Backbone.Marionette.ItemView
    template: Templates.simple_blog_info

  class SimpleBlogListView extends Backbone.Marionette.CompositeView
    childView: SimpleBlogInfoView
    template: Templates.simple_blog_list
    
  class NewBlogFormView extends FormViews.FormView
    template: Templates.new_blog_form_view
    ui:
      blog_name: '[name="blog_name"]'

    updateModel: ->
      collection = MSGBUS.reqres.request 'bumblr:get_local_blogs'
      collection.add_blog @ui.blog_name.val()

    saveModel: ->
      console.log 'called saveModel'
      collection = MSGBUS.reqres.request 'bumblr:get_local_blogs'
      collection.save()

    onSuccess: ->
      console.log 'onSuccess called'
      r = new Backbone.Router
      r.navigate '#demo/listblogs', trigger:true
  
    createModel: ->
      #collection = MSGBUS.reqres.request 'bumblr:get_local_blogs'
      #console.log collection
      #newmodel = collection.create()
      #window.newmodel = newmodel
      #return newmodel
      return new Backbone.Model url:'/'
      
        
      
      
        
                
  class MainBumblrView extends Backbone.Marionette.ItemView
    template: Templates.main_bumblr_view

  class BumblrDashboardView extends Backbone.Marionette.ItemView
    template: Templates.bumblr_dashboard_view
    
  class ShowPageView extends Backbone.Marionette.ItemView
    template: Templates.page_view


  class SimpleBlogPostView extends Backbone.Marionette.ItemView
    template: Templates.simple_post_view
    #tagName: 'span'
    className: 'col-md-2'
    
  class BlogPostListView extends Backbone.Marionette.CompositeView
    template: Templates.simple_post_page_view
    childView: SimpleBlogPostView
    className: 'row'
    events:
      'click #next-page-button': 'get_next_page'
      'click #prev-page-button': 'get_prev_page'

    get_next_page: () ->
      @collection.getNextPage()

    get_prev_page: () ->
      @collection.getPreviousPage()
      
  module.exports =
    SideBarView: SideBarView
    MainBumblrView: MainBumblrView
    BumblrDashboardView: BumblrDashboardView
    SimpleBlogListView: SimpleBlogListView
    BlogPostListView: BlogPostListView
    NewBlogFormView: NewBlogFormView
    
    