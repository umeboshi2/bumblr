define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  ########################################
  # Models
  ########################################
  class BaseModel extends Backbone.Model
    parse: (response) ->
      response.data
    
  class SimpleMeetingModel extends BaseModel

  module.exports =
    SimpleMeetingModel: SimpleMeetingModel
