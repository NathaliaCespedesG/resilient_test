import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { DeviceField } from '@shared/models/app-config';

@Component({
  selector: 'app-summary-card',
  templateUrl: './summary-card.component.html',
  styleUrl: './summary-card.component.scss'
})
export class SummaryCardComponent implements OnInit{
  @Input() deviceField: DeviceField;
  @Output() deviceFieldSelected: EventEmitter<DeviceField> = new EventEmitter<DeviceField>();


  constructor() {
    this.deviceField = {
      fieldName: '',
      label: '',
      iconPath: '',
      units: '',
    }
  }

  ngOnInit(): void {
    console.log(this.deviceField);

    if (this.deviceField.hidden == undefined) {
      this.deviceField.hidden = true;
    }
  }

  onCardClick() {
    console.log(this.deviceField.hidden);

    this.deviceField.hidden = !this.deviceField.hidden;
    this.deviceFieldSelected.emit(this.deviceField);
  }
}
