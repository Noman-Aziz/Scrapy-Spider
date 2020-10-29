import scrapy


class PeopleSpider(scrapy.Spider):
    name = 'people'
    allowed_domains = ['www.comparis.ch']
    start_urls = ['https://www.comparis.ch/gesundheit/arzt/kanton-zuerich']
    base_url = 'https://www.comparis.ch/gesundheit/arzt/kanton-zuerich?page='
    next_page_number = 2

    # INITIALIZING EVERYTHING WITH NULL
    telephone = []
    www = []
    address = []
    title = ""
    first_name = ""
    sur_name = ""
    gender = ""
    company = []
    specialization = ""
    street = []
    zip_code = []
    town = []

    # THIS FUNCTION CLEARS EVERYTHING
    def clear_everything(self):

        self.telephone = []
        self.www = []
        self.address = []
        self.title = ""
        self.first_name = ""
        self.sur_name = ""
        self.gender = ""
        self.company = []
        self.specialization = ""
        self.street = []
        self.zip_code = []
        self.town = []

    # THIS IS USED TO FETCH PERSON DATA
    def fetch_person_data(self, response):

        # GRABBING SPECIALIZATION
        self.specialization = response.xpath(
            "//p[@class='css-t3u0pg']/text()").get()

        # GRABBING FULL NAME
        full_name = response.xpath(
            "//h1[@class='css-v6hrb0 excbu0j3']/text()").get()

        # SPLITTING NAMES INTO REQUIRED COMPONENTS
        fname_flag = False

        for one in full_name.split():
            if "Dr" in one:
                self.title = one
            elif "(" in one:
                if self.title == "":
                    self.title = one
                else:
                    self.title = self.title + ' ' + one
            elif "." in one:
                if self.title == "":
                    self.title = one
                else:
                    self.title = self.title + ' ' + one
            elif fname_flag == False:
                fname_flag = True
                self.first_name = one
            elif fname_flag == True:
                if self.sur_name == "":
                    self.sur_name = one
                else:
                    self.sur_name = self.sur_name + ' ' + one

        # GRABBING GENDER
        self.gender = response.xpath(
            "//div[@class='css-15beg4l']/p[@class='css-llj5db']/text()").get()

        # GRABBING COMPANY
        self.company = response.xpath(
            "//div[@class='css-15dj4ut']/text()").getall()

        # GRABBING THINGS FROM A SINGLE COMPANY TAG
        for one_company in response.xpath("//div[@class='css-vduae0']"):
            self.telephone.append(one_company.xpath(
                ".//a[@class='css-77d8df']/text()").get())
            self.www.append(one_company.xpath(
                ".//a[@class='css-o7nw02']/@href").get())
            self.address.append(one_company.xpath(
                ".//div[@class='css-139pk9']/p[@class='css-llj5db']/text()").get())

        # SPLITTING ADDRESSES IN REQUIRED FIELDS
        for one in self.address:
            one_street = ""
            one_town = ""
            street_flag = False

            for o in one.split():
                if street_flag == False:
                    if one_street == "":
                        one_street = o.replace(',', '')
                    elif len(str(o.replace(',', ''))) == 4 and o.isdigit() == True:
                        self.zip_code.append(o)
                        street_flag = True
                    else:
                        one_street = one_street + ' ' + o.replace(',', '')
                else:
                    if one_town == "":
                        one_town = o.replace(',', '')
                    else:
                        one_town = one_town + ' ' + o.replace(',', '')

            self.street.append(one_street)
            self.town.append(one_town)

    # THIS FUNCTION FETCHES COMPANY DATA
    def fetch_company_data(self, response):

        self.company = response.xpath(
            "//h1[@class='css-v6hrb0 excbu0j3']/text()").get()
        self.telephone = response.xpath(
            "(//a[@class='css-77d8df'])[1]/text()").get()
        self.www = response.xpath("//a[@class='css-o7nw02']/@href").get()
        address = response.xpath(
            "(//div[@class='css-139pk9']/p[@class='css-llj5db'])[1]/text()").get()

        one_street = ""
        one_town = ""
        street_flag = False

        for o in address.split():
            if street_flag == False:
                if one_street == "":
                    one_street = o.replace(',', '')
                elif len(str(o.replace(',', ''))) == 4 and o.isdigit() == True:
                    self.zip_code.append(o)
                    street_flag = True
                else:
                    one_street = one_street + ' ' + o.replace(',', '')
            else:
                if one_town == "":
                    one_town = o.replace(',', '')
                else:
                    one_town = one_town + ' ' + o.replace(',', '')

        self.street.append(one_street)
        self.town.append(one_town)

    def parse(self, response):
        people = response.xpath("//a[@class='css-14yxdzk excbu0j4']")

        for person in people:
            person_url = person.xpath(".//@href").extract_first()

            if "https://www.comparis.ch" not in person_url:
                person_url = "https://www.comparis.ch" + person_url

            yield scrapy.Request(person_url, callback=self.parse_person)

        # THE NEXT PAGE HANDLING ON THE WEBSITE WAS DONE WITH JAVASCRIPT SO I USED MY OWN METHOD OF GOING TO NEXT PAGE
        next_page_url = self.base_url + str(self.next_page_number)

        if self.next_page_number < 251:
            self.next_page_number = self.next_page_number + 1

            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_person(self, response):

        # IF THERE IS A SECOND TAG OF OPENING HOURS IN WEBPAGE THEN WE HAVE COMPANY DATA AND NOT PERSON DATA
        company_only_flag = False
        oh_response = response.xpath(
            "(//h2[@class='css-1obf64m'])[2]/text()").get()
        if str(oh_response) == 'Öffnungszeiten':
            company_only_flag = True

        # clearing everything
        self.clear_everything()

        if company_only_flag == False:
            self.fetch_person_data(response)

            for i in range(len(self.address)):

                yield {
                    'Title': self.title,
                    'First Name': self.first_name,
                    'Surname': self.sur_name,
                    'Specialization': self.specialization,
                    'Gender': self.gender,
                    'Company': self.company[i],
                    'Telephone': self.telephone[i],
                    'WWW': self.www[i],
                    'E-Mail': None,
                    'Street': self.street[i],
                    'Zip': self.zip_code[i],
                    'Town': self.town[i],
                }

        else:
            self.fetch_company_data(response)

            yield {
                'Title': self.title,
                'First Name': self.first_name,
                'Surname': self.sur_name,
                'Specialization': self.specialization,
                'Gender': self.gender,
                'Company': self.company,
                'Telephone': self.telephone,
                'WWW': self.www,
                'E-Mail': None,
                'Street': self.street,
                'Zip': self.zip_code,
                'Town': self.town,
            }

