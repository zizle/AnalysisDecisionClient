# _*_ coding:utf-8 _*_
# @File  : multipart.py
# @Time  : 2020-07-21 15:42
# @Author: zizle
from PyQt5.QtNetwork import QHttpPart, QHttpMultiPart, QNetworkRequest
from PyQt5.QtCore import QFileInfo


def generate_multipart_data(text_dict=None, file_dict=None):
    multipart_data = QHttpMultiPart(QHttpMultiPart.FormDataType)
    if text_dict:
        for key, value in text_dict.items():
            text_part = QHttpPart()
            text_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data;name=\"%s\"" % key)
            text_part.setBody(str(value).encode("utf-8"))
            multipart_data.append(text_part)
    if file_dict:
        for key, file in file_dict.items():
            file_part = QHttpPart()
            filename = QFileInfo(file.fileName()).fileName()
            file_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"%s\"; filename=\"%s\"" % (key, filename))
            file_part.setBodyDevice(file)
            file.setParent(multipart_data)
            multipart_data.append(file_part)
    return multipart_data

