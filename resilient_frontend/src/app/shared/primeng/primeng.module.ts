import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { ProgressBarModule } from 'primeng/progressbar';
import { MultiSelectModule } from 'primeng/multiselect';
import { SliderModule } from 'primeng/slider';
import { DialogModule } from 'primeng/dialog';
import {ProgressSpinnerModule} from 'primeng/progressspinner';
import {DynamicDialogModule} from 'primeng/dynamicdialog';
import {SelectButtonModule} from 'primeng/selectbutton';
import { AccordionModule } from 'primeng/accordion';
import {ConfirmDialogModule} from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    ButtonModule,
    IconFieldModule,
    InputIconModule,
    TableModule,
    DropdownModule,
    ProgressBarModule,
    MultiSelectModule,
    SliderModule,
    DialogModule,
    ProgressSpinnerModule,
    DynamicDialogModule,
    SelectButtonModule,
    AccordionModule,
    ConfirmDialogModule
  ],
  exports: [
    ButtonModule,
    IconFieldModule,
    InputIconModule,
    TableModule,
    DropdownModule,
    ProgressBarModule,
    MultiSelectModule,
    SliderModule,
    DialogModule,
    ProgressSpinnerModule,
    DynamicDialogModule,
    SelectButtonModule,
    AccordionModule,
    ConfirmDialogModule
  ],
  providers: [ConfirmationService]
})
export class PrimengModule { }
