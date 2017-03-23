__copyright__   = "Copyright 2011 SFCTA"
__license__     = """
    This file is part of DTA.

    DTA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    DTA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with DTA.  If not, see <http://www.gnu.org/licenses/>.
"""


import numpy as np
from copy import deepcopy
from operator import imul, itemgetter
from itertools import izip, count, chain, ifilter
import time
import pickle 

def any(seq, pred=None):
    "Returns True if pred(x) is true for at least one element in the iterable"
    for elem in ifilter(pred, seq):
        return True
    return False

class CrossProduct(object):
    
    def __init__(self, sequences):
        """sequences is a list containing iterables e.g. [[1,2], [3,4]]"""
        self.sequences = sequences 

    def __iter__(self):

        self.wheels = map(iter, self.sequences)
        self.digits = [it.next() for it in self.wheels]
        self.index = 0
        return self

    def next(self):

        if self.index == 0:
            self.index += 1
            return self.digits

        while True:
            for i in range(len(self.digits)-1, -1, -1):
                try:
                    self.digits[i] = self.wheels[i].next()
                    self.index += 1

                    return copy(self.digits)

                except StopIteration:
                    self.wheels[i] = iter(self.sequences[i])
                    self.digits[i] = self.wheels[i].next()
            else:
                raise StopIteration

class MultiArray(object):
    """Multidimentinal array of custom numpy data types supporting
    string indices, arbitrary slicing and aggregation"""

    @classmethod
    def unpickle(cls, fileName):
        """Unpickle and return the multiarray saved in the given file"""
        inputStream = open(fileName, 'rb')
        ma = pickle.load(inputStream)
        inputStream.close()
        return ma 

    @classmethod
    def read(cls , fileName):
        '''Read the multiArray from disk and return it'''
        data = np.load(fileName)        
        numArrays = len(data.files)
        dimElements = []
        for i in range(numArrays - 1):            
            dimElements.append(data['arr_%d' % i])
        numpyArray = data['arr_%d' % (numArrays - 1)]
        ma = MultiArray('d', dimElements, numpyArray=numpyArray)
        return ma
        
    def __init__(self, dtype, dimElements, numpyArray=None, isBase=True):
        
        #TODO: you should check that all the elelmets of a dimention 
        # have the same type
        self._shape = tuple(map(len, dimElements))        
        if len(dimElements) > 0 and numpyArray is None:
            # you instantiate a numpy array 
            self._data = np.zeros(self._shape, dtype=dtype)
        elif len(dimElements) > 0 and numpyArray is not None:
            if type(numpyArray) != np.ndarray:
                raise ValueError("A numpy array is expected")
            if numpyArray.shape != self._shape:
                raise ValueError("The shape of the numpy array provided: %s is not "
                                 " the same as the dimentions of the cartesian "
                                 "product of the dimention elements %s" % \
                                     ((str(numpyArray.shape)), str(self._shape)))
            self._data = numpyArray
#            self._flatData = numpyArray.ravel()
        else:
            raise ValueError("Wrong arguments in the MultiArray constructor")
        # the translation is a list dict of pairs dimElements found in the *args and 
        # their index. Example HBW:0, HBO:1....
        self._translation = [dict(izip(element, count())) for element in dimElements]
        self._base = isBase
        self._elementsOfAllDimentions = self.getElementsOfAllDimentions()

    def getNumDim(self):
        """Return the number of dimentions"""
        return len(self._shape)

    def getShape(self):
        """Return a tupble of integers indicating the size of the array in 
        each dimention"""
        return self._data.shape

    def getSize(self):
        """Return the number of items stored in the array"""
        return self._data.size
    
    def getDataType(self):
        """Return the data type of the elements in the array"""
        return self._data.dtype
    
    def getItemSize(self):
        """Return the element byte size"""
        return self._data.itemsize
        
    def getElementsOfDimention(self, dimIndex):
        """Returns a tuple of all the indices of the dimention provided"""
        if dimIndex < 0 or dimIndex > self.getNumDim() - 1:
            return ValueError("Dim Index out of range (0, %d)" % self.getNumDim() - 1)
        return tuple(map(itemgetter(0), sorted(self._translation[dimIndex].iteritems(), key=itemgetter(1))))

    def getElementsOfAllDimentions(self):
        """Return a tuple with the elements of all dimentions"""
        return tuple([self.getElementsOfDimention(i) for i in range(self.getNumDim())])

    def changeTranslationForDim(self, dimIndex, oldElementsToNew):
        
        if len(oldElementsToNew) != len(self._translation[dimIndex]):
            raise ValueError("The dimention of the new translation should be the same as the the old one")
        if set(oldElementsToNew.keys()) != set(self._translation[dimIndex].keys()):
            raise ValueError("You must provide a mapping between all the old elements of"
                             "the dimention and the new ones")
        if len(set(oldElementsToNew.values())) != len(self._translation[dimIndex]):
            raise ValueError("There elements for the new dimention have duplicate values")
        
        #TODO I do dot like this part code. Can you write it in one line? YES you can
#        newMapping = dict(((oldElementsToNew[oldElem], iIndex) for izip....

        newMapping = {}
        for oldElement, internalIndex in self._translation[dimIndex].iteritems():
            newElement = oldElementsToNew[oldElement]
            newMapping[newElement] = internalIndex
        self._translation[dimIndex] = newMapping
        
    def __str__(self):
        """Convert the array into its string numpy representation"""
        result = "Dimention elements:"
        for i, dim in enumerate(self._translation):
            result += "dim%d: %s\n" % (i, str(np.array(self.getElementsOfDimention(i))))
        result += "\nData:\n"
        result += str(self._data)
        return result

    def asPrettyString(self):
        """Return the array as a properly formated string"""

        if self.getNumDim() != 2:
            raise MultiArrayError("The number of dimentions should be two to call this method")
        
        elementsOfDim0 = map(str, self.getElementsOfDimention(0))
        elementsOfDim1 = map(str, self.getElementsOfDimention(1))

        maxLenOfDim0 = max(map(len, elementsOfDim0))
        maxLenOfDim1 = max(map(len, elementsOfDim1))

        maxLenElem = max(map(len, map(str, self)))
        columnLength = max(maxLenOfDim1, maxLenElem)

        formatString = "%" + str(maxLenOfDim0 + 2) + "s" + ("%" + str(columnLength + 2) + "s") * self.getShape()[1] + "\n"
        result = formatString % tuple(chain([""], elementsOfDim1)) 
        for i in self.getElementsOfDimention(0):
            result += formatString % tuple(chain([str(i)], map(str, self[i, :])))
        return result 

    def asPrettyString4(self):
        """Return a four dimentional array as a property formated string"""
        #TODO this is monkey patching. To do it properly for all dimentions and not 
        #only 4 you have to create a slice 
        #object!!! 
        if self.getNumDim() != 4:
            raise MultiArrayError("The number of dimentions should be four to call this method")

        result = ""
        for element0 in getElementsOfDimention(0):
            for element1 in getElementsOfDimention(1):
                result += "Dim0: %s Dim1: %s\n\t%s\n" % (element0, element1, self[element0, element1, :, :].asPrettyString())
        
    def _translateElement(self, dimIndex, element):
        """Return the corresponding index of the provided element and dimention"""
        try:
            return self._translation[dimIndex][element]
        except KeyError, e:
            raise IndexError("Dim %d does not have element %s" % (dimIndex, str(element)))
            
    def _translateElements(self, *args):
        """Return a list with the translated indices"""
        return tuple([self._translateElement(dimIndex, elem) \
                    for dimIndex, elem in enumerate(args)])

    def __getitem__(self, viewElements):

        #if you have a one dimentional array
        if isinstance(viewElements, str) or isinstance(viewElements, int):
            if self.getNumDim() != 1:
                raise IndexError("Invalid Index")
            return deepcopy(self._data.item(self._translateElement(0, viewElements)))
        
        if len(viewElements) != self.getNumDim():
            raise IndexError("Invalid Index")
        
        #if instead of a slice a list is entered raise an error
        if any(viewElements, pred=lambda elem: isinstance(elem, list)):
            raise ValueError("Not implemented yet")
        #if any of the indices entered is a slice then translate the slice and return a new MultiArray
        #with a referece to the data
        elif any(viewElements, pred=lambda elem: isinstance(elem, slice)):
            viewObj, newDimElements = self._translateViewObject(viewElements)
            return MultiArray("d", newDimElements, numpyArray=self._data[viewObj], isBase=False)
        #if no slice object is ented => the user has asked for an individual element. So,
        #return a deepcopy of the element
        else:
            return deepcopy(self._data.item(*self._translateElements(*viewElements)))

    def _translateViewObject(self, eViewObject):
        """Translate the external view object to the internal one"""
        
        translatedViewObj = []
        newDimElements = []
        for dimIndex, viewElement in enumerate(eViewObject):
            if isinstance(viewElement, slice):
                if viewElement.step is not None:
                    raise IndexError("Strides are not supported (yet)")
                baseStart = None
                if viewElement.start != None:
                    baseStart = self._translateElement(dimIndex, viewElement.start)
                baseStop = None
                if viewElement.stop != None:
                    baseStop = self._translateElement(dimIndex, viewElement.stop)
                if baseStart and baseStop and baseStop <= baseStart:
                    raise IndexError("The stop element %s of dimention %d cannot be to the"
                                     "left of the start element %s of the same dimention" 
                                     % (baseStop, dimIndex, baseStart))
                baseSlice = slice(baseStart, baseStop, None)
                translatedViewObj.append(baseSlice)
                elements = self.getElementsOfDimention(dimIndex)[baseSlice]
                newDimElements.append(elements)
            else:
                translatedViewObj.append(self._translateElement(dimIndex, viewElement))
        return translatedViewObj, newDimElements

    def __setitem__(self, viewElements, value):

        if len(viewElements) != self.getNumDim():
            raise IndexError("Invalid Index dimentions")

        if any(viewElements, pred=lambda elem: isinstance(elem, list)):
            raise ValueError("Not implemented yet")
        elif any(viewElements, pred=lambda elem: isinstance(elem, slice)):
            viewObj, newDimElements = self._translateViewObject(viewElements)
            if isinstance(value, MultiArray):
                if self._data[viewObj].shape != value.getShape():
                    raise ValueError("The MultiArray's shape %s is not the same with the view's "
                                     "shape %s" % (self._data[viewObj].shape, value.getShape()))
                self._data[viewObj] = value.getNumpyArray()
            elif isinstance(value, list):
                if len(value) != self.getSize():
                    raise ValueError("The length of the list is not the same with the number of"
                                     "elements of the MultiArray")
                self._data[viewObj] = value
            elif isinstance(value, np.ndarray):
                if self._data[viewObj].shape == value.shape:
                    self._data[viewObj] = value
                else:
                    raise ValueError("The numpy array's shape %s is not the same with " 
                                     "the view's shape %s" % (str(self._data[viewObj].shape), str(value.shape)))
                                     
            elif isinstance(value, int) or isinstance(value, float):
                self._data[viewObj] = value
            else:
                raise ValueError("Unsupported type. Use a numpy array or a list instead")            
        else:
            self._data.__setitem__(self._translateElements(*viewElements), value)
        #if it is an iterable such as multi array then you create a
        #numpy array out of this? YES

    def __eq__(self, other):
        """Return true if the two arrays are of the same shape and 
        have the same values"""
        if not isinstance(other, MultiArray):
            raise ValueError("I cannot compare a MultiArray with an object of"
                             "type: %s" % type(other))
        if self.getElementsOfAllDimentions() != \
                other.getElementsOfAllDimentions():
            #print "getElememOfAllDimentions"
            return False
        
        if self.getSize() == self._data.size:
            comp = self._data == other._data
            if np.sum(comp) == self.getSize():
                return True
            else:
                return False
        else:
            return False

    def __iter__(self):
        #todo 
        return self._data.flat
   
    def fill(self, value):

        self._data.fill(value)

#        if self._base == True:
#            self._data.fill(value)            
#        else:
#            raise ValueError("Not implemented yet")
        
    def iterkeys(self):
        elems = self.getElementsOfAllDimentions()
        return iter(CrossProduct(elems))

    def itervalues(self):
        """return an iterator over the values"""
        return self.__iter__()
      
    def iteritems(self):
        
        elems = self.getElementsOfAllDimentions()
        for element in CrossProduct(elems):
            yield element, self[element]

    def eliminateDimention(self, dimIndex):
        """Return the sum accross dimention dimIndex"""
        dimElements = self.getElementsOfDimention(dimIndex)
        marginals = self._data.sum(dimIndex)
        newDimElements = list(self.getElementsOfAllDimentions())
        newDimElements.pop(dimIndex)
        return MultiArray(self._data.dtype, newDimElements, numpyArray=marginals )
    
    def __mul__(self, scalarValue):
        """Return a new multiArray with its values multiplied by the 
        provided scalar value"""
        #TODO you can probably have vectors or other values provided that the 
        # resulting array has the same size with self. Hmmm hwy does it have to have the 
        #same size? Well if it does not how are you going to name the new dimentions?
        
        newData = self._data * scalarValue
        return MultiArray("d", self._elementsOfAllDimentions, newData)

    def __div__(self, scalarValue):
        """Return a new multiArray with its values divided by the proded
        scalr value"""
        if scalarValue == 0:
            raise ValueError("I cannot divide with zero")
        if self._base == True:
            return self.__mul__(1 / scalarValue)
        else:
            raise ValueError("Not implemented yet")

    def __add__(self, value):
        """Add a scalar or a MultiArray to this array and 
        return a new MultiArray"""
                
        if isinstance(value, int) or isinstance(value, float):
            newData = self._data + deepcopy(value)
        elif isinstance(value, MultiArray):
            if not self.getSize() == value.getSize():
                raise ValueError("I cannot add MultiArrays of different sizes")
            newData = self._data + value._data
        else:
            raise ValueError("I cannot add %s and a MultiArray" % str(type(value)))
        return MultiArray("d", self._elementsOfAllDimentions, newData)

    def __sub__(self, value):
        """Add a scalar or a MultiArray to this array and 
        return a new MultiArray"""
        #TODO it has the excact same implementation with add
        # you ought to remove the duplication in code

        if isinstance(value, int) or isinstance(value, float):
            newData = self._data - deepcopy(value)
        elif isinstance(value, MultiArray):
            if not self.getSize() == value.getSize():
                raise ValueError("I cannot add MultiArrays of different sizes")
            newData = self._data - value._data
        else:
            raise ValueError("I cannot add %s and a MultiArray" % str(type(value)))
        return MultiArray("d", self._elementsOfAllDimentions, newData)

    def multiplyInPlace(self, value):
        """Multiply all the items of the array with the provided value"""
        self._data *= value

    def getNumpyArray(self):
        """Return a reference to the stored data as multidimentional numpy array"""
        return self._data

    def getSum(self):
        """return the sum of all the items in the array"""
        return np.sum(self._data)

#        if self._base == True:
#            return np.sum(self._data)
#        else:
#            raise ValueError("Not implemented yet")

    def copy(self):
        
        """Return a copy of the current Multi Array"""
        if not self._base:
            raise ValueError("Not implemented yet")
        
        raise ValueError("not implemented yet")
        copyData = self._data.copy()
        return MultiArray("d", self._elementsOfAllDimentions, copyData)

    def expand(self, alphaToBeta):
        """Expands the current dimentions of multiArray.

        Input a numpy array with the following fields "alpha", "beta", "percentage"
        Output: a new Multi Array 
        """
        if self.getNumDim() != 2:
            raise ValueError("I can only expand a 2D array")
        if self.getShape()[0] != self.getShape()[1]:
            raise ValueError("I can only expand a square 2D array")
        if set(self.getElementsOfDimention(0)) != set(self.getElementsOfDimention(1)):
            raise ValueError("The elements of the two dimentions of the array are not the same"
                             "and as a consequence the array cannot be expanded")
        if set(alphaToBeta["beta"]) != set(self.getElementsOfDimention(0)):
            raise ValueError("The beta values are not the same with the elements of the"
                             "MultiArray")

        numAlphas = len(alphaToBeta)
        percentages = np.zeros((numAlphas, 1))
        for i in xrange(numAlphas):
            percentages[i, 0] = alphaToBeta[i]["percentage"]
        newData = np.dot(percentages, percentages.transpose())

        betas = list(self.getElementsOfDimention(0))
        betaIndex = [0] * numAlphas
        for i, beta in enumerate(alphaToBeta["beta"]):
            betaIndex[i] = betas.index(beta)

        
        for i in xrange(numAlphas):
            betaI = betaIndex[i]
            for j in xrange(numAlphas):
                newData[i, j] *= self._data[betaI, betaIndex[j]]

        result = MultiArray("d", [alphaToBeta["alpha"], alphaToBeta["alpha"]], newData)            
        return result

    def collapse(self, alphaToBeta):
        """Collapses the current array into fewer dimensions
        input: a numpy array with the following fields "alpha", "beta", 
        "percentage". The current zoneIds are in the "alpha" fields, the 
        new ones in the "beta" fields."""
        
        #check that you have all the alphas
        #check that you have a 2D array

        newDimention = len(set(alphaToBeta["beta"]))
        result = numpy.zeros(newDimention **2, "d")
        a2b = dict(izip(alphaToBeta["alpha"], alphaToBeta["beta"]))

        for alphaOrigin in self.getDimIndices(0):
            for alphaDestination in self.getDimIndices(1):
                betaOrigin = a2b[alphaOrigin]
                betaDestination = a2b[alphaDestination]
                value = self.getValue(alphaOrigin, alphaDestination)
                result.addInPlace(betaOrigin, betaDestination, value)
        return result
    
    def writeToCSV(self, fileName):
        """Save the multiarry as a comma delimited text file"""
        np.savetxt(fileName, self._data, delimiter=',', fmt='%d')

    def pickle(self, fileName):
        """Save the pickled multiarray in the given file"""
        outputStream = open(fileName, 'wb')
        pickle.dump(self, outputStream)
        outputStream.close()

    def write(self, fileName):
        """Write the multidimentional array to file using the numpy binary format"""
        data = []
        for dim in range(self.getNumDim()):
            dimElements = self.getElementsOfDimention(dim)
            data.append(dimElements)
        data.append(self._data)
        np.savez(fileName, *data)
            
