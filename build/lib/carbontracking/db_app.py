from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
#import geocoder

### APP CONFIGURATION ###
app = Flask(__name__)
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' 
db = SQLAlchemy(app)

### DATABASE MODELS ###
train_devices = db.Table('train_devices',
    db.Column('hostgpu_id', db.Integer, db.ForeignKey('hostgpu.id'), primary_key=True),
    db.Column('tracking_info_id', db.String, db.ForeignKey('trackinginfo.id'), primary_key=True),
    db.Column('CO2_usage', db.Float, nullable=True),
    db.Column('power_usg', db.Float, nullable=True)
)

inference_devices = db.Table('inference_devices',
    db.Column('hostgpu_id', db.Integer, db.ForeignKey('hostgpu.id'), primary_key=True),
    db.Column('inference_info_id', db.String, db.ForeignKey('inferenceinfo.id'), primary_key=True),
    db.Column('CO2_usage', db.Float, nullable=True)
)

class Trackinginfo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[int] = mapped_column(unique=True)
    carbon_intensity: Mapped[float] = mapped_column(unique=False)
    power_usage: Mapped[float] = mapped_column(unique=False)
    CO2_usage: Mapped[float] = mapped_column(unique=False)
    model: Mapped[str] = mapped_column(unique=False)
    elapsed_time: Mapped[float] = mapped_column(unique=False)
    CO2_inference: Mapped[float] = mapped_column(unique=False, nullable=True)
    task_model: Mapped[str] = mapped_column(unique=False)
    task_name = db.Column(db.Integer, db.ForeignKey('task.task'), nullable=False)
    train_devices = db.relationship('Hostgpu', secondary=train_devices, lazy='subquery',
            backref=db.backref('trackinginfo', lazy=True))

    def __repr__(self):
        return f"Trackinginfo(id={self.id}, timestamp={self.timestamp}, " \
               f"carbon_intensity={self.carbon_intensity}, power_usage={self.power_usage}, " \
               f"CO2_usage={self.CO2_usage}, task_name={self.task_name}, model={self.model}, " \
               f"elapsed_time={self.elapsed_time}, CO2_inference={self.CO2_inference}, task_model={self.task_model})"
    
class Inferenceinfo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp_inf: Mapped[int] = mapped_column(unique=True)
    carbon_intensity_inf: Mapped[float] = mapped_column(unique=False)
    power_usage_inf: Mapped[float] = mapped_column(unique=False)
    CO2_usage_inf: Mapped[float] = mapped_column(unique=False)
    model_inf: Mapped[str] = mapped_column(unique=False)
    task_model_inf: Mapped[str] = mapped_column(unique=False)
    elapsed_time_inf: Mapped[float] = mapped_column(unique=False)
    task_name_inf = db.Column(db.Integer, db.ForeignKey('task.task'), nullable=False)
    inf_devices = db.relationship('Hostgpu', secondary=inference_devices, lazy='subquery',
        backref=db.backref('inferenceinfo', lazy=True))

    def __repr__(self):
        return f"Inferenceinfo(id={self.id}, timestamp_inf={self.timestamp_inf}, " \
                f"carbon_intensity_inf={self.carbon_intensity_inf}, power_usage_inf={self.power_usage_inf}, " \
                f"CO2_usage_inf={self.CO2_usage_inf}, task_name_inf={self.task_name_inf}, " \
                f"model_inf={self.model_inf}, elapsed_time_inf={self.elapsed_time_inf}, task_model_inf={self.task_model_inf})"

hostgpus = db.Table('hostgpus',
    db.Column('hostgpu_host', db.Integer, db.ForeignKey('hostgpu.id'), primary_key=True),
    db.Column('task_id', db.String, db.ForeignKey('task.task'), primary_key=True)
)

class Task(db.Model):
    #id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task: Mapped[str] = mapped_column(primary_key=True, unique=True)
    track_infos = db.relationship('Trackinginfo', backref='tasks', lazy=True)
    inference_infos = db.relationship('Inferenceinfo', backref='tasks', lazy=True)

    tags = db.relationship('Hostgpu', secondary=hostgpus, lazy='subquery',
        backref=db.backref('tasks', lazy=True))
    
    models = db.relationship('Model', backref='tasks', lazy=True)

    def __repr__(self):
        return f"Task(task={self.task})"

class Model(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(unique=False)
    task = db.Column(db.Integer, db.ForeignKey('task'), nullable=False)

    def __repr__(self):
        return f"Model(id={self.id}, model_name={self.model_name}, task_id={self.task})"

class Hostgpu(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    host: Mapped[str] = mapped_column(unique=False)
    gpu_cpu: Mapped[str] = mapped_column(unique=False)

    def __repr__(self):
        return f"HostGPU(id={self.id}, host={self.host}, gpu_model={self.gpu_cpu})"


class Powermix(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[int] = mapped_column(unique=False)
    powermix: Mapped[str] = mapped_column(unique=False)

    def __repr__(self):
        return f"Powermix(id={self.id}, timestamp={self.timestamp}, powermix={self.powermix})"