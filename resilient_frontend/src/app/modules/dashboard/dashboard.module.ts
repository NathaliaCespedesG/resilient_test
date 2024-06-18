import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardComponent } from './dashboard.component';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { ParticipantsComponent } from './components/participants/participants.component';
import { ReportsComponent } from './components/reports/reports.component';
import { DevicesComponent } from './components/devices/devices.component';
import { MaterialModule } from '../../shared/material/material.module';
import { PrimengModule } from '../../shared/primeng/primeng.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ParticipantSummaryComponent } from './components/participant-summary/participant-summary.component';



@NgModule({
  declarations: [
    DashboardComponent,
    ParticipantsComponent,
    ReportsComponent,
    DevicesComponent,
    ParticipantSummaryComponent,
  ],
  imports: [
    CommonModule,
    DashboardRoutingModule,
    MaterialModule,
    PrimengModule,
    FormsModule,
    ReactiveFormsModule
  ]
})
export class DashboardModule { }
