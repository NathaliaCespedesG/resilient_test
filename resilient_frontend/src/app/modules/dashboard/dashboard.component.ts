import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {

  constructor(
    private _router: Router
  ){}

  onClickOption(option: string): void {
    this._router.navigate(['/dashboard/' + option]);
  }

}
