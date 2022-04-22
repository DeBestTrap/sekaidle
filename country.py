import math

class Country:
  def __init__(self, code_, name_, latitude_, longitude_, aliases_=None):
    self.code = code_
    self.name = name_
    self.latitude = float(latitude_) * math.pi / 180
    self.longitude = float(longitude_) * math.pi / 180
    self.aliases = aliases_

  def returnCoord(self):
    return (self.latitude, self.longitude)

  def distanceTo(self, coord):
    latitude_, longitude_ = coord
    a = math.sin((self.latitude - latitude_)/2)**2 + math.cos(self.latitude)*math.cos(latitude_)*((math.sin((self.longitude - longitude_)/2))**2)
    c = 2*(math.atan2(math.sqrt(a), math.sqrt(1-a)))
    bearing =  math.atan2(math.sin(longitude_-self.longitude)*math.cos(latitude_), math.cos(self.latitude)*math.sin(latitude_) - math.sin(self.latitude)*math.cos(latitude_)*math.cos(longitude_-self.longitude))
    return ((bearing*180/math.pi)+360)%360, 6378.1370*c