import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MaterialModule } from './material/material.module';
import { LayoutModule } from './layout/layout.module';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    MaterialModule,
    LayoutModule
  ],
  exports: [
    MaterialModule,
    LayoutModule
  ]
})
export class SharedModule { }
