define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  PageableCollection = require 'backbone.paginator'
  qs = require 'querystring'
    
  ########################################
  # Base Models
  ########################################

  class BaseLocalStorageModel extends Backbone.Model
    initialize: () ->
      @fetch()
      @on 'change', @save, @

    fetch: () ->
      console.log '===== FETCH FIRED LOADING LOCAL STORAGE ===='
      @set JSON.parse localStorage.getItem @id

    save: (attributes) ->
      console.log '===== CHANGE FIRED SAVING LOCAL STORAGE ===='
      localStorage.setItem(@id, JSON.stringify(@toJSON()))

    destroy: (options) ->
      console.log '===== DESTROY LOCAL STORAGE ===='
      localStorage.removeItem @id

    isEmpty: () ->
      _.size @attributes <= 1
      

  ########################################
  # stuff
  ########################################
  baseURL = 'http://api.tumblr.com/v2'

  class TumblrClient
    tagged: (tag, options, callback) ->
      options = options || {}
      options.tag = tag
      @_get '/tagged', options, callback, true

    _get: (path, params, callback, addApiKey) ->
      params = params || {}
      if addApiKey
        params.api_key = @credentials.consumer_key

      $.getJSON baseURL + path + '?callback=?', params, callback
        
        

  ########################################
  # Test Tumblr Models and collections
  ########################################
  #
  class BaseTumblrModel extends Backbone.Model
    baseURL: baseURL
  
  class BlogInfo extends BaseTumblrModel
    url: () ->
      @baseURL + '/blog/' + @id + '/info?api_key=' + @api_key + '&callback=?'
    parse: (response) ->
      blog = response.response.blog
      @set 'id', blog.name
      return blog
      
      
    
  class Post extends BaseTumblrModel

  class LocalBlogModel extends Backbone.Model

    
  class LocalBlogCollection extends Backbone.Collection
    initialize: () ->
      settings = MSGBUS.reqres.request 'bumblr:get_app_settings'
      @api_key = settings.get 'consumer_key'
      @fetch()
      @on 'change', @save, @
      
    fetch: () ->
      console.log '===========fetching local blogs========='
      blogs = JSON.parse(localStorage.getItem('bumblr_blogs')) || []
      @set blogs
      
    save: (collection) ->
      console.log '===========saving local blogs========='
      localStorage.setItem('bumblr_blogs', JSON.stringify(@toJSON()))

    add_blog: (name) ->
      sitename = name + '.tumblr.com'
      model = new BlogInfo
      model.set 'id', sitename
      model.api_key = @api_key
      @add model
      model.fetch()
      

  class PhotoPostCollection extends Backbone.Collection
    url: () ->
      baseURL + '/' + @id + '/posts/photo' + '?callback=?'
      
  class BlogPosts extends Backbone.Collection
    baseURL: baseURL
    url: () ->
      url = @baseURL + '/blog/' + @base_hostname + '/posts/photo?api_key='
      url = url + @api_key + '&callback=?'
      return url
    parse: (response) ->
      response.response.posts

  make_blog_post_collection = (base_hostname) ->
    settings = MSGBUS.reqres.request 'bumblr:get_app_settings'
    api_key = settings.get 'consumer_key'
    bp = new BlogPosts
    bp.api_key = api_key
    bp.base_hostname = base_hostname
    console.log 'bp.api_key is ' + bp.api_key
    console.log 'bp.url() is ' + bp.url()
    return bp
    
  req = 'bumblr:make_blog_post_collection'
  MSGBUS.reqres.setHandler req, (base_hostname) ->
    make_blog_post_collection(base_hostname)
    
  ########################################
  # Models
  ########################################

  class Page extends Backbone.Model
    url: () ->
      pathname = '/bumblr/pages/'
      if window.location.pathname == '/index.local.html'
        pathname = '/pages/'
      return pathname + @id + '.json'

  class BumblrSettings extends BaseLocalStorageModel
    id: 'bumblr_settings'

  #bumblr_settings = new BumblrSettings id:'bumblr'
  bumblr_settings = new BumblrSettings
  MSGBUS.reqres.setHandler 'bumblr:get_app_settings', ->
    bumblr_settings
      
  client = new TumblrClient
  settings = MSGBUS.reqres.request 'bumblr:get_app_settings'
  client.credentials = settings.attributes
  MSGBUS.reqres.setHandler 'bumblr:get_tumblr_client', ->
    client
    
  local_blogs = new LocalBlogCollection
  MSGBUS.reqres.setHandler 'bumblr:get_local_blogs', ->
    local_blogs

     
  module.exports =
    Page: Page
    BlogPosts: BlogPosts
    
