import { Component, OnInit, ViewChild } from '@angular/core';
import { RequestsService } from '../../../../services/requests.service';
import { Role } from '../../../../shared/models/roles';
import { User, Users } from '../../../../shared/models/database-types';
import { NgModel } from '@angular/forms';

@Component({
  selector: 'app-participants',
  templateUrl: './participants.component.html',
  styleUrl: './participants.component.scss'
})
export class ParticipantsComponent implements OnInit {
  participants: User[] = [];
  filteredParticipants: User[] = [];
  roles: Role[] = [];
  selectedRole: Role;
  showDialog: boolean = false;
  username: string;
  showSpinner: boolean = false;
  isDuplicateUsername: boolean = false;
  isAddParticipantSuccessful: boolean = false;
  usernameFilter: string = '';
  withingsAuthURL: string = 'https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc&redirect_uri=https%3A%2F%2Fresilient.ukdri.care%2F&scope=user.activity%2Cuser.metrics%2Cuser.info%2Cuser.sleepevents%2Cuser.rawdata&state=vsGpqaNPVDPOCrik8Fwn1F4369nTHa'

  @ViewChild('usernameInput', { static: false }) usernameInput?: NgModel;

  constructor(
    private _requestsService: RequestsService
  ) {

    this.roles = [
      {name: 'PARTICIPANT'},
      {name: 'TEST'}
    ];

    this.selectedRole = this.roles[0];
    this.username = '';
  }

  ngOnInit(): void {
    this.getUsers();
  }

  getUsers(): void{
    this._requestsService.getUsers().subscribe({
      next: (answer: Users) => {
        if (answer) {
          const usersArray: User[] = Object.values(answer.users);
          this.participants = usersArray.filter( user => {
            const role = user['role'].toLowerCase();
            return role !== 'admin' && role !== 'clinician' && role != 'super_admin';

          });
          this.filteredParticipants = this.participants;
        }
      }
    });
  }

  applyUsernameFilter(): void {
    this.filteredParticipants = this.participants.filter(participant => {
      return participant.username.toLowerCase().includes(this.usernameFilter.toLowerCase());
    });
  }

  onUsernameInputChange(): void {
    this.isDuplicateUsername = false;
  }

  showAddParticipantModal(): void {
    this.showDialog = true;
    if (this.usernameFilter) {
      this.username = this.usernameFilter
    }
  }

  addParticipant(): void{

    this.showSpinner = true;

    const participantData = {
      username: this.username,
      role: this.selectedRole.name,
      password_hash: "NA"
    }
    this._requestsService.addParticipant(participantData).subscribe({
      next: (response) => {
        this.showSpinner = false;
        this.isAddParticipantSuccessful = true;
      },
      error: (error) => {
        this.isDuplicateUsername = error.error.username.status_code = 403 ? true : false;
        this.showSpinner = false;
      }
    }
    );
  }

  onDialogHide(): void {
    if (this.isAddParticipantSuccessful){
      this.getUsers();
    }
    this.username = '';
    this.showSpinner = false;
    this.isAddParticipantSuccessful = false;
    this.isDuplicateUsername = false;
    if (this.usernameInput) {
      this.usernameInput.control.markAsPristine(); // Reset ngModel state on dialog show
      this.usernameInput.control.markAsUntouched();
    }
  }

}
